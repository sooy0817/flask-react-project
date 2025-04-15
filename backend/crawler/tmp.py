import winreg  # Windows 전용 라이브러리

# 📁 DLL 경로 (현재 위치에 맞게 수정하세요!)
dll_path = r"C:\FilePathCheckerModuleExample.dll"

# 📂 레지스트리 경로
reg_path = r"Software\HNC\HwpCtrl\Modules"

try:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
        winreg.SetValueEx(key, "FilePathCheckerModuleExample", 0, winreg.REG_SZ, dll_path)
        print(f"✅ 레지스트리 등록 완료!\n→ {reg_path} 에 {dll_path} 등록됨")
except Exception as e:
    print(f"❌ 등록 실패: {e}")
