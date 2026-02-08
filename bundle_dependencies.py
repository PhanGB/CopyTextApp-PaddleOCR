# -*- coding: utf-8 -*-
import os
import sys
import shutil

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def get_build_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'CopyTextApp')

def bundle_paddleocr_models():
    print("\n[1/2] Đang bundle PaddleOCR models...")
    build_dir = get_build_dir()
    models_dir = os.path.join(build_dir, 'paddleocr_models')

    if os.path.exists(models_dir):
        print("  ✅ PaddleOCR models đã được bundle")
        return True

    user_models_dir = os.path.join(os.path.expanduser('~'), '.paddleocr')
    if os.path.exists(user_models_dir):
        try:
            print("  Đang copy PaddleOCR models từ user directory...")
            os.makedirs(models_dir, exist_ok=True)
            shutil.copytree(user_models_dir, models_dir)
            print("  ✅ Đã copy PaddleOCR models")
            return True
        except Exception as e:
            print(f"  ⚠️  Lỗi khi copy models: {str(e)}")

    print("  ⚠️  Không tìm thấy PaddleOCR models.")
    print("  💡 Models sẽ được tải khi app chạy lần đầu.")
    return False

def bundle_easyocr_models():
    print("\n[2/2] Đang bundle EasyOCR models...")
    build_dir = get_build_dir()
    models_dir = os.path.join(build_dir, 'easyocr_models')
    
    if os.path.exists(models_dir):
        print("  ✅ EasyOCR models đã được bundle")
        return True
    
    user_models_dir = os.path.join(os.path.expanduser('~'), '.EasyOCR', 'model')
    if os.path.exists(user_models_dir):
        try:
            print("  Đang copy EasyOCR models từ user directory...")
            os.makedirs(models_dir, exist_ok=True)
            shutil.copytree(user_models_dir, os.path.join(models_dir, 'model'))
            print("  ✅ Đã copy EasyOCR models")
            return True
        except Exception as e:
            print(f"  ⚠️  Lỗi khi copy models: {str(e)}")
    
    print("  ⚠️  Không tìm thấy EasyOCR models.")
    print("  💡 Models sẽ được tải khi app chạy lần đầu.")
    return False

def main():
    print("="*60)
    print("BUNDLE DEPENDENCIES")
    print("="*60)
    print()
    
    build_dir = get_build_dir()
    if not os.path.exists(build_dir):
        print("❌ Thư mục build chưa tồn tại!")
        print("Vui lòng chạy build.bat trước.")
        return 1
    
    bundle_paddleocr_models()
    bundle_easyocr_models()
    
    print()
    print("="*60)
    print("✅ Hoàn tất!")
    print("="*60)
    return 0

if __name__ == '__main__':
    sys.exit(main())

