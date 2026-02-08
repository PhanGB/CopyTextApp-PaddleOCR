# -*- coding: utf-8 -*-
"""
CopyText App Installer
Tác giả: Bùi Quang Tiến THĐD
"""
import os
import sys
import shutil
import subprocess
import ctypes

APP_NAME = "CopyText App"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Bùi Quang Tiến THĐD"
INSTALL_DIR = os.path.join(os.getenv('PROGRAMFILES', 'C:\\Program Files'), 'CopyTextApp') 
USER_INSTALL_DIR = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local')), 'CopyTextApp')

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if is_admin():
        return True
    else:
        print("⚠️  Cần quyền Administrator để cài đặt!")
        print("Đang yêu cầu quyền Admin...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{__file__}"', None, 1
            )
        except:
            print("❌ Không thể chạy với quyền Admin!")
            input("Nhấn Enter để thoát...")
        return False

def copy_easyocr_models(install_dir):
    print("  • Đang copy EasyOCR models...")
    
    source_models = os.path.join(os.path.dirname(__file__), 'easyocr_models')
    if not os.path.exists(source_models):
        print("  ⚠️  Không tìm thấy EasyOCR models trong package.")
        return False

def copy_paddleocr_models(install_dir):
    print("  • Đang copy PaddleOCR models...")

    source_models = os.path.join(os.path.dirname(__file__), 'paddleocr_models')
    if not os.path.exists(source_models):
        print("  ⚠️  Không tìm thấy PaddleOCR models trong package.")
        return False

    dest_models = os.path.join(install_dir, 'paddleocr_models')
    try:
        if os.path.exists(dest_models):
            shutil.rmtree(dest_models)
        shutil.copytree(source_models, dest_models)
        print("  ✅ Đã copy PaddleOCR models")
        return True
    except Exception as e:
        print(f"  ⚠️  Lỗi khi copy models: {str(e)}")
        return False
    
    dest_models = os.path.join(install_dir, 'easyocr_models')
    try:
        if os.path.exists(dest_models):
            shutil.rmtree(dest_models)
        shutil.copytree(source_models, dest_models)
        print(f"  ✅ Đã copy EasyOCR models")
        return True
    except Exception as e:
        print(f"  ⚠️  Lỗi khi copy models: {str(e)}")
        return False

def create_shortcuts(exe_path):
    print("\n[3/3] Đang tạo shortcuts...")
    
    shortcuts_created = 0
    
    try:
        # Tạo shortcut trên Desktop
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        if os.path.exists(desktop):
            desktop_shortcut = os.path.join(desktop, f'{APP_NAME}.lnk')
            vbs_script = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{desktop_shortcut}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{exe_path}"
oLink.WorkingDirectory = "{os.path.dirname(exe_path)}"
oLink.Description = "{APP_NAME} - Trích xuất text từ hình ảnh"
oLink.Save
'''
            vbs_file = os.path.join(os.path.dirname(exe_path), 'create_desktop_shortcut.vbs')
            with open(vbs_file, 'w', encoding='utf-8') as f:
                f.write(vbs_script)
            
            subprocess.run(['cscript', '//nologo', vbs_file], capture_output=True)
            if os.path.exists(vbs_file):
                os.remove(vbs_file)
            
            if os.path.exists(desktop_shortcut):
                print(f"  ✅ Đã tạo shortcut trên Desktop")
                shortcuts_created += 1
    except Exception as e:
        print(f"  ⚠️  Lỗi khi tạo shortcut Desktop: {str(e)}")
    
    try:
        # Tạo shortcut trong Start Menu
        start_menu = os.path.join(os.getenv('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        if not os.path.exists(start_menu):
            start_menu = os.path.join(os.getenv('PROGRAMDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        
        if os.path.exists(start_menu):
            start_menu_shortcut = os.path.join(start_menu, f'{APP_NAME}.lnk')
            vbs_script = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{start_menu_shortcut}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{exe_path}"
oLink.WorkingDirectory = "{os.path.dirname(exe_path)}"
oLink.Description = "{APP_NAME} - Trích xuất text từ hình ảnh"
oLink.Save
'''
            vbs_file = os.path.join(os.path.dirname(exe_path), 'create_startmenu_shortcut.vbs')
            with open(vbs_file, 'w', encoding='utf-8') as f:
                f.write(vbs_script)
            
            subprocess.run(['cscript', '//nologo', vbs_file], capture_output=True)
            if os.path.exists(vbs_file):
                os.remove(vbs_file)
            
            if os.path.exists(start_menu_shortcut):
                print(f"  ✅ Đã tạo shortcut trong Start Menu")
                shortcuts_created += 1
    except Exception as e:
        print(f"  ⚠️  Lỗi khi tạo shortcut Start Menu: {str(e)}")
    
    return shortcuts_created > 0

def main():
    print("="*60)
    print(f"  {APP_NAME} v{APP_VERSION}")
    print(f"  Tác giả: {APP_AUTHOR}")
    print("="*60)
    print()
    
    if not is_admin():
        print("⚠️  Cần quyền Administrator để cài đặt!")
        print("Đang yêu cầu quyền Admin...")
        run_as_admin()
        return
    
    print("Đang cài đặt app...")
    print()
    
    exe_source = 'CopyTextApp.exe'
    if not os.path.exists(exe_source):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        exe_source = os.path.join(script_dir, 'CopyTextApp.exe')
        if not os.path.exists(exe_source):
            print("❌ Không tìm thấy file CopyTextApp.exe!")
            print("Vui lòng chạy installer từ thư mục chứa file .exe")
            input("\nNhấn Enter để thoát...")
            return
    
    install_dir = INSTALL_DIR
    try:
        os.makedirs(install_dir, exist_ok=True)
    except PermissionError:
        install_dir = USER_INSTALL_DIR
        os.makedirs(install_dir, exist_ok=True)
        print(f"⚠️  Không thể cài vào Program Files. Cài vào: {install_dir}")
    
    print(f"[1/3] Đang copy files vào: {install_dir}")
    
    try:
        # Đóng app nếu đang chạy
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'CopyTextApp.exe', '/T'], 
                         capture_output=True, timeout=5)
            import time
            time.sleep(1)
        except:
            pass
        
        exe_path = os.path.join(install_dir, 'CopyTextApp.exe')
        
        # Xóa file cũ nếu tồn tại
        if os.path.exists(exe_path):
            try:
                os.remove(exe_path)
            except:
                # Nếu không xóa được, đổi tên
                try:
                    os.rename(exe_path, exe_path + '.old')
                except:
                    pass
        
        shutil.copy2(exe_source, exe_path)
        print(f"  ✅ Đã copy CopyTextApp.exe")
        
        files_to_copy = [
            'HUONG_DAN_CAI_DAT_CHO_NGUOI_KHAC.md',
            'LICENSE.txt'
        ]
        
        for file in files_to_copy:
            if os.path.exists(file):
                try:
                    shutil.copy2(file, os.path.join(install_dir, file))
                    print(f"  ✅ Đã copy {file}")
                except:
                    pass
        
        print("\n[2/3] Đang copy OCR models...")
        copy_easyocr_models(install_dir)
        copy_paddleocr_models(install_dir)
        
    except Exception as e:
        print(f"❌ Lỗi khi copy files: {str(e)}")
        print(f"💡 Thử đóng app CopyTextApp nếu đang chạy, sau đó chạy lại Setup.exe")
        input("\nNhấn Enter để thoát...")
        return
    
    create_shortcuts(exe_path)
    
    print()
    print("="*60)
    print("✅ CÀI ĐẶT HOÀN TẤT!")
    print("="*60)
    print()
    print(f"App đã được cài đặt tại: {install_dir}")
    print("Bạn có thể tìm app trên Desktop hoặc chạy từ:")
    print(f"  {exe_path}")
    print()
    print("🚀 Bạn có muốn chạy app ngay bây giờ không? (Y/N): ", end='')
    
    try:
        choice = input().strip().upper()
        if choice == 'Y':
            subprocess.Popen([exe_path])
    except:
        pass
    
    input("\nNhấn Enter để thoát...")

if __name__ == '__main__':
    main()
