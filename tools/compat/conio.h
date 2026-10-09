/* Linux stand-in for the Windows console header used by the book's demo programs. */
#pragma once
static inline int _getch(void) { return 0; }   /* "Press any key" pauses return at once */
static inline int _kbhit(void) { return 0; }   /* "Press ESC to stop" checks never fire */
