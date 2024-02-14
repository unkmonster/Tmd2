// dllmain.cpp : 定义 DLL 应用程序的入口点。
#include "pch.h"

#include <pybind11/embed.h>
#include <spdlog/spdlog.h>

#include "utility.h"
#include "ThreadPool.h"

std::atomic_flag gRunning = ATOMIC_FLAG_INIT;

BOOL WINAPI HandlerRoutine(DWORD dwCtrlType) {
    if (dwCtrlType == CTRL_C_EVENT) {
        static std::once_flag called;
        std::call_once(called, []() {gRunning.clear(); });
        return TRUE;
    }
    return FALSE;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hModule);
        SetConsoleOutputCP(CP_UTF8);
        setlocale(LC_ALL, ".utf-8");
        setlocale(LC_TIME, "C");
        SetConsoleCtrlHandler(HandlerRoutine, TRUE);

        spdlog::set_pattern("%Y-%m-%d %X [%^%l%$] %v");
        spdlog::set_level(spdlog::level::info);  // Set global log level to info

        gRunning.test_and_set();
    }
    return TRUE;
}

