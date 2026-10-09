//+------------------------------------------------------------------+
//| OpeningCandle_EA.mq5                                             |
//| Opening-candle strategy for US stock and index CFDs.             |
//| At 10:00 New York, trade in the direction of the first 30-minute |
//| candle of the US session, stop at its far end, exit just before  |
//| the 16:00 New York close. One trade per symbol per day. Fed      |
//| decision days are skipped. Every trade is appended to a CSV in   |
//| the common Files folder, in the journal's column order.          |
//| Put one copy on each symbol's chart (any timeframe).             |
//+------------------------------------------------------------------+
#property copyright "cs"
#property version   "1.00"
#include <Trade\Trade.mqh>

enum ENUM_DST_RULE { DST_US = 0, DST_EU = 1, DST_NONE = 2 };

input group "Risk and prop-firm rules"
input double RiskPct          = 0.5;    // Risk per trade, % of balance
input double MaxDailyLossPct  = 5.0;    // Max daily loss, % of start balance
input double MaxLossPct       = 10.0;   // Max total loss, % of start balance
input double StartBalance     = 0;      // Challenge start balance (0 = balance at first run)
input bool   StopOnBreach     = true;   // Close and stop when a limit is hit
input bool   AllowReal        = false;  // Allow trading on a real-money account

input group "Strategy"
input int    OpeningBars      = 1;      // Opening candle length in 30-min bars (1 = 30 min)
input double TargetR          = 0;      // Take profit in R (0 = none, exit at the close)
input int    EntryHourNY      = 10;     // Entry hour, New York time
input int    EntryMinuteNY    = 0;      // Entry minute
input int    EntryWindowMin   = 5;      // Still enter up to this many minutes late
input int    ExitHourNY       = 15;     // Exit hour, New York time
input int    ExitMinuteNY     = 59;     // Exit minute (stocks stop trading at 16:00)
input bool   SkipFedDays      = true;   // Skip Fed decision days (from the MT5 calendar)
input string FedDatesFallback = "2026.10.28,2026.12.09"; // Used only if the calendar is unavailable
input bool   NewsAvoid        = false;  // Delay the entry while a high-impact USD release is within 2 minutes

input group "Server clock"
input int    ServerGmtWinter  = 2;      // Server UTC offset in winter (FTMO: 2)
input ENUM_DST_RULE ServerDst = DST_US; // Server daylight-saving rule (FTMO: US)

input group "Identification and logging"
input long   MagicNumber      = 0;      // 0 = automatic from the symbol name
input string LogFile          = "OpeningCandle_trades.csv"; // In the common Files folder
input int    SlippagePoints   = 50;     // Max slippage, points

CTrade   trade;
long     g_magic = 0;
double   g_startBalance = 0;
datetime g_dayKey = 0;            // Prague date of the current risk day
double   g_dayStartEquity = 0;
bool     g_stopped = false;
string   g_stopReason = "";
bool     g_dayBlocked = false;    // daily loss hit today
datetime g_lastTradeDay = 0;      // New York date of the last entry (or decision not to trade)
datetime g_fedDay = 0;            // New York date the Fed check was made for
bool     g_isFedDay = false;
datetime g_delayUntil = 0;        // news delay (UTC)
string   g_note = "starting";
// open / last trade
ulong    g_posTicket = 0;
long     g_posId = 0;
int      g_dir = 0;
double   g_entry = 0, g_sl = 0, g_tp = 0, g_lots = 0, g_riskMoney = 0, g_riskPct = 0;
datetime g_entryNy = 0;

//+------------------------------------------------------------------+
//| small helpers                                                    |
//+------------------------------------------------------------------+
string GV(string k) { return "OC_" + _Symbol + "_" + k; }
void   GVSet(string k, double v) { GlobalVariableSet(GV(k), v); }
double GVGet(string k) { return GlobalVariableCheck(GV(k)) ? GlobalVariableGet(GV(k)) : 0; }
datetime DateOf(datetime t) { return (datetime)((long)t - ((long)t % 86400)); }
datetime MakeDate(int y, int m, int d) { return StringToTime(StringFormat("%04d.%02d.%02d 00:00", y, m, d)); }

bool UsDst(datetime utc)
  {
   MqlDateTime t; TimeToStruct(utc, t);
   datetime mar1 = MakeDate(t.year, 3, 1);  MqlDateTime m; TimeToStruct(mar1, m);
   int firstSunMar = 1 + ((7 - m.day_of_week) % 7);
   datetime start = mar1 + (datetime)((firstSunMar - 1 + 7) * 86400 + 7 * 3600);   // 2nd Sunday of March, 02:00 EST
   datetime nov1 = MakeDate(t.year, 11, 1); MqlDateTime n; TimeToStruct(nov1, n);
   int firstSunNov = 1 + ((7 - n.day_of_week) % 7);
   datetime end = nov1 + (datetime)((firstSunNov - 1) * 86400 + 6 * 3600);         // 1st Sunday of November, 02:00 EDT
   return (utc >= start && utc < end);
  }
bool EuDst(datetime utc)
  {
   MqlDateTime t; TimeToStruct(utc, t);
   datetime mar31 = MakeDate(t.year, 3, 31); MqlDateTime m; TimeToStruct(mar31, m);
   datetime start = mar31 - (datetime)(m.day_of_week * 86400) + 3600;
   datetime oct31 = MakeDate(t.year, 10, 31); MqlDateTime o; TimeToStruct(oct31, o);
   datetime end = oct31 - (datetime)(o.day_of_week * 86400) + 3600;
   return (utc >= start && utc < end);
  }
int ServerOffsetHours(datetime utcApprox)
  {
   int dst = 0;
   if(ServerDst == DST_US) dst = UsDst(utcApprox) ? 1 : 0;
   else if(ServerDst == DST_EU) dst = EuDst(utcApprox) ? 1 : 0;
   return ServerGmtWinter + dst;
  }
datetime ServerToUtc(datetime s) { return s - (datetime)(ServerOffsetHours(s - (datetime)(ServerGmtWinter * 3600)) * 3600); }
datetime UtcToServer(datetime u) { return u + (datetime)(ServerOffsetHours(u) * 3600); }
datetime UtcToNy(datetime u)     { return u - (datetime)((UsDst(u) ? 4 : 5) * 3600); }
datetime NyToUtc(datetime ny)    { datetime u0 = ny + 5 * 3600; return ny + (datetime)((UsDst(u0) ? 4 : 5) * 3600); }
datetime NowUtc()                { return ServerToUtc(TimeTradeServer()); }
datetime NowNy()                 { return UtcToNy(NowUtc()); }
datetime PragueDate(datetime utc){ return DateOf(utc + (datetime)((EuDst(utc) ? 2 : 1) * 3600)); }

string ClockStatus()
  {
   int measured = (int)MathRound((double)((long)TimeTradeServer() - (long)TimeGMT()) / 3600.0);
   int expected = ServerOffsetHours(TimeGMT());
   if(measured == expected) return StringFormat("clock: OK, server is UTC%+d", measured);
   return StringFormat("clock: WARNING server is UTC%+d but settings expect UTC%+d", measured, expected);
  }
bool ClockOk()
  {
   int measured = (int)MathRound((double)((long)TimeTradeServer() - (long)TimeGMT()) / 3600.0);
   return measured == ServerOffsetHours(TimeGMT());
  }

double ValuePerUnitPerLot()
  {
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(ts > 0 && tv > 0) return tv / ts;
   return SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
  }
double NormalizeLots(double lots)
  {
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double mx = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step <= 0) step = mn > 0 ? mn : 0.01;
   lots = MathFloor(lots / step + 1e-9) * step;
   if(lots > mx) lots = mx;
   if(lots < mn) return 0;
   return NormalizeDouble(lots, 8);
  }

//+------------------------------------------------------------------+
//| positions and log                                                |
//+------------------------------------------------------------------+
bool FindPosition(ulong &ticket, long &id)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != g_magic) continue;
      ticket = t; id = (long)PositionGetInteger(POSITION_IDENTIFIER);
      return true;
     }
   return false;
  }

void SaveTradeState()
  {
   GVSet("posId", (double)g_posId); GVSet("posTicket", (double)g_posTicket);
   GVSet("dir", g_dir); GVSet("entry", g_entry); GVSet("sl", g_sl); GVSet("tp", g_tp);
   GVSet("lots", g_lots); GVSet("riskMoney", g_riskMoney); GVSet("riskPct", g_riskPct);
   GVSet("entryNy", (double)(long)g_entryNy);
  }
void LoadTradeState()
  {
   g_posId = (long)GVGet("posId"); g_posTicket = (ulong)GVGet("posTicket");
   g_dir = (int)GVGet("dir"); g_entry = GVGet("entry"); g_sl = GVGet("sl"); g_tp = GVGet("tp");
   g_lots = GVGet("lots"); g_riskMoney = GVGet("riskMoney"); g_riskPct = GVGet("riskPct");
   g_entryNy = (datetime)(long)GVGet("entryNy");
  }
void ClearTradeState()
  {
   g_posId = 0; g_posTicket = 0; g_dir = 0; g_entry = 0; g_sl = 0; g_tp = 0; g_lots = 0; g_riskMoney = 0; g_riskPct = 0; g_entryNy = 0;
   SaveTradeState();
  }

void LogTrade(double exitPx, string why, double netProfit)
  {
   int h = FileOpen(LogFile, FILE_READ | FILE_WRITE | FILE_CSV | FILE_COMMON | FILE_ANSI, ',');
   if(h == INVALID_HANDLE) { Print("OpeningCandle: cannot open log ", LogFile, " error ", GetLastError()); return; }
   if(FileSize(h) == 0)
      FileWrite(h, "Date", "Setup", "Direction", "Lots", "Entry", "Stop loss", "Take profit", "Exit", "Exit reason", "Followed rules?", "Notes");
   FileSeek(h, 0, SEEK_END);
   double r = (g_riskMoney > 0) ? netProfit / g_riskMoney : 0;
   int dg = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   FileWrite(h, TimeToString(g_entryNy, TIME_DATE), "OpeningCandle " + _Symbol, (g_dir > 0 ? "Buy" : "Sell"),
             DoubleToString(g_lots, 2), DoubleToString(g_entry, dg), DoubleToString(g_sl, dg),
             (g_tp > 0 ? DoubleToString(g_tp, dg) : ""), DoubleToString(exitPx, dg), why, "Yes",
             StringFormat("R=%+.3f net=%.2f risk%%=%.2f", r, netProfit, g_riskPct));
   FileClose(h);
   Print("OpeningCandle ", _Symbol, ": logged ", why, " R=", DoubleToString(r, 3));
  }

// the position we were managing is gone: find its closing deal, log it, clear the state
void HandleClosedPosition()
  {
   double exitPx = 0, net = 0; string why = "Close";
   if(HistorySelectByPosition(g_posId))
     {
      int n = HistoryDealsTotal();
      for(int i = 0; i < n; i++)
        {
         ulong d = HistoryDealGetTicket(i);
         if(d == 0) continue;
         if(HistoryDealGetInteger(d, DEAL_ENTRY) != DEAL_ENTRY_OUT) continue;
         exitPx = HistoryDealGetDouble(d, DEAL_PRICE);
         long reason = HistoryDealGetInteger(d, DEAL_REASON);
         if(reason == DEAL_REASON_SL) why = "Stop";
         else if(reason == DEAL_REASON_TP) why = "Target";
         else if(reason == DEAL_REASON_EXPERT) why = (g_stopped || g_dayBlocked) ? "Breach" : "Close";
         else why = "Close";
         net += HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_COMMISSION) + HistoryDealGetDouble(d, DEAL_SWAP);
        }
      // the opening deal's commission counts too
      for(int i = 0; i < n; i++)
        {
         ulong d = HistoryDealGetTicket(i);
         if(d != 0 && HistoryDealGetInteger(d, DEAL_ENTRY) == DEAL_ENTRY_IN)
            net += HistoryDealGetDouble(d, DEAL_COMMISSION);
        }
     }
   LogTrade(exitPx, why, net);
   g_note = StringFormat("last trade %s %s, R=%+.2f", (g_dir > 0 ? "buy" : "sell"), why, (g_riskMoney > 0 ? net / g_riskMoney : 0));
   ClearTradeState();
  }

//+------------------------------------------------------------------+
//| Fed decision day (MT5 calendar; its times = UTC + current offset)|
//+------------------------------------------------------------------+
bool IsFedDay(datetime nyDate)
  {
   int off = (int)MathRound((double)((long)TimeTradeServer() - (long)TimeGMT()) / 3600.0);
   datetime fromUtc = NyToUtc(nyDate) - 6 * 3600, toUtc = NyToUtc(nyDate) + 30 * 3600;
   MqlCalendarValue vals[];
   ResetLastError();
   if(CalendarValueHistory(vals, fromUtc + (datetime)(off * 3600), toUtc + (datetime)(off * 3600), NULL, "USD"))
     {
      for(int i = 0; i < ArraySize(vals); i++)
        {
         MqlCalendarEvent ev;
         if(!CalendarEventById(vals[i].event_id, ev)) continue;
         if(ev.importance != CALENDAR_IMPORTANCE_HIGH) continue;
         if(StringFind(ev.name, "Interest Rate Decision") < 0) continue;
         datetime evUtc = vals[i].time - (datetime)(off * 3600);
         if(DateOf(UtcToNy(evUtc)) == nyDate) return true;
        }
      return false;
     }
   Print("OpeningCandle: calendar unavailable (error ", GetLastError(), "), using the fallback Fed dates");
   string parts[];
   int n = StringSplit(FedDatesFallback, ',', parts);
   for(int i = 0; i < n; i++)
     {
      StringTrimLeft(parts[i]); StringTrimRight(parts[i]);
      if(parts[i] == "") continue;
      if(DateOf(StringToTime(parts[i])) == nyDate) return true;
     }
   return false;
  }

// is a high-impact USD release within 2 minutes of now? (only used when NewsAvoid is on)
bool NewsNearby(datetime &eventUtc)
  {
   int off = (int)MathRound((double)((long)TimeTradeServer() - (long)TimeGMT()) / 3600.0);
   datetime now = NowUtc();
   MqlCalendarValue vals[];
   if(!CalendarValueHistory(vals, now - 3600 + (datetime)(off * 3600), now + 3600 + (datetime)(off * 3600), NULL, "USD")) return false;
   for(int i = 0; i < ArraySize(vals); i++)
     {
      MqlCalendarEvent ev;
      if(!CalendarEventById(vals[i].event_id, ev) || ev.importance != CALENDAR_IMPORTANCE_HIGH) continue;
      datetime evUtc = vals[i].time - (datetime)(off * 3600);
      if(MathAbs((double)((long)evUtc - (long)now)) <= 120) { eventUtc = evUtc; return true; }
     }
   return false;
  }

//+------------------------------------------------------------------+
//| risk limits                                                      |
//+------------------------------------------------------------------+
void UpdateRiskDay()
  {
   datetime today = PragueDate(NowUtc());
   if(today != g_dayKey)
     {
      g_dayKey = today;
      g_dayStartEquity = MathMax(AccountInfoDouble(ACCOUNT_EQUITY), AccountInfoDouble(ACCOUNT_BALANCE));
      g_dayBlocked = false;
      GVSet("dayKey", (double)(long)g_dayKey); GVSet("dayStart", g_dayStartEquity);
     }
  }
void CheckLimits()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(!g_stopped && eq <= g_startBalance * (1.0 - MaxLossPct / 100.0))
     {
      g_stopped = true; g_stopReason = StringFormat("max loss hit: equity %.2f", eq); GVSet("stopped", 1);
      Print("OpeningCandle ", _Symbol, ": ", g_stopReason);
     }
   if(!g_dayBlocked && (eq - g_dayStartEquity) <= -g_startBalance * MaxDailyLossPct / 100.0)
     {
      g_dayBlocked = true;
      Print("OpeningCandle ", _Symbol, ": daily loss limit hit, no more trades today");
     }
   if((g_stopped || g_dayBlocked) && StopOnBreach && g_posTicket != 0 && PositionSelectByTicket(g_posTicket))
      trade.PositionClose(g_posTicket, (ulong)SlippagePoints);
  }

//+------------------------------------------------------------------+
//| entry                                                            |
//+------------------------------------------------------------------+
void TryEntry(datetime nyNow)
  {
   datetime nyDate = DateOf(nyNow);
   MqlDateTime d; TimeToStruct(nyNow, d);
   if(d.day_of_week == 0 || d.day_of_week == 6) return;
   if(g_lastTradeDay == nyDate) return;                       // already decided today
   datetime entryAt = nyDate + (datetime)(EntryHourNY * 3600 + EntryMinuteNY * 60);
   if(nyNow < entryAt) { g_note = "waiting for the 10:00 New York entry"; return; }
   int window = EntryWindowMin + (NewsAvoid ? 5 : 0);
   if(nyNow >= entryAt + (datetime)(window * 60)) { g_lastTradeDay = nyDate; GVSet("lastTradeDay", (double)(long)nyDate); g_note = "entry window missed today"; return; }
   if(g_stopped || g_dayBlocked) return;
   if(!ClockOk()) { g_note = "clock mismatch, not trading"; return; }
   if(SkipFedDays)
     {
      if(g_fedDay != nyDate) { g_isFedDay = IsFedDay(nyDate); g_fedDay = nyDate; }
      if(g_isFedDay) { g_lastTradeDay = nyDate; GVSet("lastTradeDay", (double)(long)nyDate); g_note = "Fed decision day, skipped"; return; }
     }
   if(NewsAvoid)
     {
      datetime ev;
      if(NowUtc() < g_delayUntil) { g_note = "waiting out a news release"; return; }
      if(NewsNearby(ev)) { g_delayUntil = ev + 150; g_note = "news within 2 minutes, delaying entry"; return; }
     }
   // the opening candle(s): the session's first M30 bar opens at 09:30 New York
   datetime openBar = UtcToServer(NyToUtc(nyDate + (datetime)(9 * 3600 + 30 * 60)));
   int shift = iBarShift(_Symbol, PERIOD_M30, openBar, true);
   if(shift < 0) { g_note = "opening bar not found (holiday?)"; return; }
   if(shift < OpeningBars) { g_note = "opening candle still forming"; return; }
   int last = shift - (OpeningBars - 1);
   double o = iOpen(_Symbol, PERIOD_M30, shift), c = iClose(_Symbol, PERIOD_M30, last);
   double hi = iHigh(_Symbol, PERIOD_M30, iHighest(_Symbol, PERIOD_M30, MODE_HIGH, OpeningBars, last));
   double lo = iLow(_Symbol, PERIOD_M30, iLowest(_Symbol, PERIOD_M30, MODE_LOW, OpeningBars, last));
   if(c == o) { g_lastTradeDay = nyDate; GVSet("lastTradeDay", (double)(long)nyDate); g_note = "flat opening candle, no trade"; return; }
   int dir = (c > o) ? 1 : -1;
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask <= 0 || bid <= 0) { g_note = "no quotes yet"; return; }
   double entry = (dir > 0) ? ask : bid;
   double sl = (dir > 0) ? lo : hi;
   double risk = (entry - sl) * dir;
   if(risk <= 0) { g_lastTradeDay = nyDate; GVSet("lastTradeDay", (double)(long)nyDate); g_note = "price already beyond the stop, no trade"; return; }
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskMoney = balance * RiskPct / 100.0;
   double vpu = ValuePerUnitPerLot();
   double lots = NormalizeLots(riskMoney / (risk * vpu));
   if(lots <= 0) { g_lastTradeDay = nyDate; GVSet("lastTradeDay", (double)(long)nyDate); g_note = "risk too small for the minimum lot, no trade"; return; }
   // margin cap: the broker's own margin rule decides the leverage
   double margin = 0;
   if(OrderCalcMargin(dir > 0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, _Symbol, lots, entry, margin) && margin > 0)
     {
      double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE) * 0.9;
      if(margin > freeMargin)
        {
         lots = NormalizeLots(lots * freeMargin / margin);
         if(lots <= 0) { g_lastTradeDay = nyDate; GVSet("lastTradeDay", (double)(long)nyDate); g_note = "not enough margin, no trade"; return; }
        }
     }
   double tp = (TargetR > 0) ? entry + dir * TargetR * risk : 0;
   int dg = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   sl = NormalizeDouble(sl, dg); tp = NormalizeDouble(tp, dg);
   trade.SetExpertMagicNumber(g_magic);
   trade.SetDeviationInPoints(SlippagePoints);
   trade.SetTypeFillingBySymbol(_Symbol);
   bool sent = (dir > 0) ? trade.Buy(lots, _Symbol, 0, sl, tp, "OC") : trade.Sell(lots, _Symbol, 0, sl, tp, "OC");
   uint rc = trade.ResultRetcode();
   if(!sent || (rc != TRADE_RETCODE_DONE && rc != TRADE_RETCODE_DONE_PARTIAL && rc != TRADE_RETCODE_PLACED))
     {
      g_note = StringFormat("order failed (%u %s), retrying", rc, trade.ResultRetcodeDescription());
      Print("OpeningCandle ", _Symbol, ": ", g_note);
      return;                                                   // try again next second while the window is open
     }
   ulong t; long id;
   Sleep(500);
   if(!FindPosition(t, id)) { g_note = "order sent, waiting for the position"; return; }
   g_posTicket = t; g_posId = id; g_dir = dir;
   g_entry = PositionGetDouble(POSITION_PRICE_OPEN); g_sl = sl; g_tp = tp; g_lots = PositionGetDouble(POSITION_VOLUME);
   g_riskMoney = g_lots * (g_entry - g_sl) * dir * vpu; g_riskPct = (balance > 0) ? g_riskMoney / balance * 100.0 : 0;
   g_entryNy = nyNow;
   g_lastTradeDay = nyDate; GVSet("lastTradeDay", (double)(long)nyDate);
   SaveTradeState();
   g_note = StringFormat("%s %.2f lots at %s, stop %s, risk %.2f%%", (dir > 0 ? "bought" : "sold"), g_lots,
                         DoubleToString(g_entry, dg), DoubleToString(g_sl, dg), g_riskPct);
   Print("OpeningCandle ", _Symbol, ": ", g_note);
  }

//+------------------------------------------------------------------+
//| exit                                                             |
//+------------------------------------------------------------------+
void TryExit(datetime nyNow)
  {
   if(g_posTicket == 0) return;
   if(!PositionSelectByTicket(g_posTicket)) { HandleClosedPosition(); return; }
   datetime nyDate = DateOf(nyNow);
   datetime exitAt = DateOf(g_entryNy) + (datetime)(ExitHourNY * 3600 + ExitMinuteNY * 60);
   bool overdue = (nyNow >= exitAt);                          // includes a position carried into the next day
   if(!overdue) return;
   if(trade.PositionClose(g_posTicket, (ulong)SlippagePoints))
      g_note = "closing at the end of the session";
   else
      g_note = StringFormat("close failed (%u %s), retrying", trade.ResultRetcode(), trade.ResultRetcodeDescription());
  }

//+------------------------------------------------------------------+
void OnInit_State()
  {
   g_startBalance = (StartBalance > 0) ? StartBalance : GVGet("startBalance");
   if(g_startBalance <= 0) g_startBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   GVSet("startBalance", g_startBalance);
   g_stopped = (GVGet("stopped") > 0);
   if(g_stopped) g_stopReason = "stopped earlier after a limit breach (delete the global variables to reset)";
   g_lastTradeDay = (datetime)(long)GVGet("lastTradeDay");
   g_dayKey = (datetime)(long)GVGet("dayKey"); g_dayStartEquity = GVGet("dayStart");
   LoadTradeState();
   ulong t; long id;
   if(FindPosition(t, id))
     {
      if(g_posId != id || g_posTicket != t)
        {   // position we didn't record (restart or manual): adopt it
         g_posTicket = t; g_posId = id;
         g_dir = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 1 : -1;
         g_entry = PositionGetDouble(POSITION_PRICE_OPEN); g_sl = PositionGetDouble(POSITION_SL); g_tp = PositionGetDouble(POSITION_TP);
         g_lots = PositionGetDouble(POSITION_VOLUME);
         g_riskMoney = g_lots * MathAbs(g_entry - g_sl) * ValuePerUnitPerLot();
         g_riskPct = (AccountInfoDouble(ACCOUNT_BALANCE) > 0) ? g_riskMoney / AccountInfoDouble(ACCOUNT_BALANCE) * 100 : 0;
         g_entryNy = UtcToNy(ServerToUtc((datetime)PositionGetInteger(POSITION_TIME)));
         SaveTradeState();
        }
      g_note = "adopted the open position";
     }
   else if(g_posId != 0)
      HandleClosedPosition();                                   // it closed while the EA was off
  }

int OnInit()
  {
   g_magic = MagicNumber;
   if(g_magic == 0)
     {
      long h = 0;
      for(int i = 0; i < StringLen(_Symbol); i++) h = (h * 31 + StringGetCharacter(_Symbol, i)) % 100000;
      g_magic = 260000 + h;
     }
   trade.SetExpertMagicNumber(g_magic);
   trade.SetDeviationInPoints(SlippagePoints);
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_REAL && !AllowReal)
     {
      g_stopped = true; g_stopReason = "real-money account and AllowReal is off";
     }
   OnInit_State();
   EventSetTimer(1);
   Print("OpeningCandle ", _Symbol, " started, magic ", (int)g_magic, ", ", ClockStatus());
   return(INIT_SUCCEEDED);
  }
void OnDeinit(const int reason) { EventKillTimer(); Comment(""); }

void OnTimer()
  {
   UpdateRiskDay();
   CheckLimits();
   datetime nyNow = NowNy();
   if(g_posTicket != 0 && !PositionSelectByTicket(g_posTicket)) HandleClosedPosition();
   if(g_posTicket != 0) TryExit(nyNow);
   else if(!g_stopped) TryEntry(nyNow);
   // chart comment
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double dayPnl = (g_startBalance > 0) ? (eq - g_dayStartEquity) / g_startBalance * 100 : 0;
   double totPnl = (g_startBalance > 0) ? (eq - g_startBalance) / g_startBalance * 100 : 0;
   string pos = (g_posTicket != 0) ? StringFormat("%s %.2f lots, entry %s, stop %s", (g_dir > 0 ? "long" : "short"), g_lots,
                 DoubleToString(g_entry, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)), DoubleToString(g_sl, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS))) : "none";
   Comment(StringFormat("OpeningCandle EA  %s   magic %d\n%s\nNew York time %s\nstatus: %s\nposition: %s\n"
                        "today %+.2f%% (limit -%.0f%%)   since start %+.2f%% (limit -%.0f%%)%s%s",
                        _Symbol, (int)g_magic, ClockStatus(), TimeToString(nyNow, TIME_DATE | TIME_MINUTES), g_note, pos,
                        dayPnl, MaxDailyLossPct, totPnl, MaxLossPct,
                        (g_dayBlocked ? "\nDAILY LIMIT HIT: no more trades today" : ""),
                        (g_stopped ? "\nSTOPPED: " + g_stopReason : "")));
  }
void OnTick() { }
//+------------------------------------------------------------------+
