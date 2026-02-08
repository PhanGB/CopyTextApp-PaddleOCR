import os
import sys

def preload_easyocr_models():
    try:
        import easyocr
        print("Đang tải EasyOCR models...")
        print("Lần đầu sẽ tải khoảng 100MB, vui lòng chờ...")
        
        reader = easyocr.Reader(['vi', 'en'], gpu=False, verbose=True)
        
        print("\n✅ Đã tải xong EasyOCR models!")
        print("Models đã được lưu vào cache và sẽ không cần tải lại.")
        return True
    except ImportError:
        print("EasyOCR chưa được cài đặt. Bỏ qua preload.")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi tải models: {str(e)}")
        return False

def preload_paddleocr_models():
    try:
        from paddleocr import PaddleOCR
        print("Đang tải PaddleOCR models...")
        print("Lần đầu sẽ tải model OCR, vui lòng chờ...")

        PaddleOCR(use_angle_cls=True, lang='vi', use_gpu=False, show_log=True)

        print("\n✅ Đã tải xong PaddleOCR models!")
        print("Models đã được lưu vào cache và sẽ không cần tải lại.")
        return True
    except ImportError:
        print("PaddleOCR chưa được cài đặt. Bỏ qua preload.")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi tải models: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("PRELOAD OCR MODELS")
    print("=" * 60)
    print()

    paddle_ok = preload_paddleocr_models()
    easy_ok = preload_easyocr_models()

    if paddle_ok or easy_ok:
        print("\n✅ Hoàn tất! Models đã sẵn sàng.")
    else:
        print("\n⚠️  Không thể preload models.")
    
    input("\nNhấn Enter để thoát...")

