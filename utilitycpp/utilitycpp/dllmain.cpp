// dllmain.cpp : 定义 DLL 应用程序的入口点。
#include "pch.h"
#include <pybind11/embed.h>
#include "utility.h"
#include <spdlog/spdlog.h>

std::atomic_flag running = ATOMIC_FLAG_INIT;

BOOL WINAPI HandlerRoutine(
    _In_ DWORD dwCtrlType
) {
    if (dwCtrlType == CTRL_C_EVENT) {
        static std::once_flag called;
        std::call_once(called, []() {running.clear(); });
        return TRUE;
    }
    return FALSE;
}

BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
                     )
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
        SetConsoleOutputCP(CP_UTF8);
        setlocale(LC_ALL, ".utf-8");
        setlocale(LC_TIME, "C");
        SetConsoleCtrlHandler(HandlerRoutine, TRUE);

        spdlog::set_pattern("%Y-%m-%d %X [%^%l%$] %v");
        spdlog::set_level(spdlog::level::info);  // Set global log level to info

        running.test_and_set();
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}

