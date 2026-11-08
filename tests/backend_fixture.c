/* Owned 32-bit process for cross-bitness Windows/Wine API tests. Not a game. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <io.h>

int wmain(int argc, wchar_t **argv) {
    if (argc != 2) return 2;
    unsigned char *page = VirtualAlloc(NULL, 8192, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (!page) return 3;
    for (unsigned int i = 0; i < 64; ++i) page[i] = (unsigned char)i;
    DWORD old;
    if (!VirtualProtect(page, 4096, PAGE_READONLY, &old)) return 4;
    volatile LONG *counter = (volatile LONG *)(page + 4096);
    wchar_t ready[32768], stop[32768], pending[32768];
    if (_snwprintf(ready, 32768, L"%ls\\ready.json", argv[1]) < 0) return 5;
    if (_snwprintf(stop, 32768, L"%ls\\stop", argv[1]) < 0) return 5;
    if (_snwprintf(pending, 32768, L"%ls\\ready.tmp", argv[1]) < 0) return 5;
    FILE *output = _wfopen(pending, L"w");
    if (!output) return 6;
    fprintf(output, "{\"pid\":%lu,\"pointer_bits\":%u,\"address\":%llu,\"counter\":%llu}",
            GetCurrentProcessId(), (unsigned)(sizeof(void *) * 8),
            (unsigned long long)(uintptr_t)page, (unsigned long long)(uintptr_t)counter);
    fclose(output);
    if (_wrename(pending, ready) != 0) return 7;
    while (_waccess(stop, 0) != 0) {
        InterlockedIncrement(counter);
        Sleep(5);
    }
    VirtualFree(page, 0, MEM_RELEASE);
    return 0;
}
