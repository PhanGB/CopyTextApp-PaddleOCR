import tkinter as tk
from tkinter import messagebox
import pyperclip
from PIL import ImageGrab, Image, ImageEnhance, ImageFilter
import sys
import os
import numpy as np
import ctypes
import traceback
import logging

def get_log_file_path():
    """Lấy đường dẫn file log trong user directory để tránh permission denied"""
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Tạo log directory trong user AppData để có quyền ghi
    user_home = os.path.expanduser('~')
    log_dir = os.path.join(user_home, 'AppData', 'Local', 'CopyTextApp')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'app_error.log')

logging.basicConfig(
    filename=get_log_file_path(),
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def safe_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Error in {func.__name__}: {str(e)}\n{traceback.format_exc()}")
        return None

USE_PADDLEOCR = False
try:
    from paddleocr import PaddleOCR
    USE_PADDLEOCR = True
except ImportError:
    pass

USE_EASYOCR = False
try:
    import easyocr
    USE_EASYOCR = True
except ImportError:
    pass

class FloatingIconApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CopyText App")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.9)
        self.root.configure(bg='black')
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        self.root.geometry('60x60+{}+{}'.format(
            self.screen_width - 80, 
            self.screen_height - 100
        ))
        
        self.tooltip = None
        self.context_menu = None
        self.easyocr_ready = False
        self.easyocr_loading = False
        self.paddleocr_ready = False
        self.paddleocr_loading = False
        
        # Copy EasyOCR models từ install directory vào user directory nếu cần
        self._copy_easyocr_models_if_needed()
        # Copy PaddleOCR models từ install directory vào user directory nếu cần
        self._copy_paddleocr_models_if_needed()
        
        self._print_welcome()
        
        self.setup_icon()
        self.setup_bindings()
        
        if USE_PADDLEOCR:
            self.root.after(100, self._preload_paddleocr)
        elif USE_EASYOCR:
            self.root.after(100, self._preload_easyocr)
    
    def _copy_easyocr_models_if_needed(self):
        """Copy EasyOCR models từ install directory vào user directory nếu chưa có"""
        if not USE_EASYOCR:
            return
        
        try:
            # Lấy app directory (nơi app được cài đặt)
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            app_models_dir = os.path.join(app_dir, 'easyocr_models', 'model')
            
            # Nếu không có models trong app directory, bỏ qua
            if not os.path.exists(app_models_dir):
                return
            
            # User directory để lưu models
            user_home = os.path.expanduser('~')
            user_models_dir = os.path.join(user_home, '.EasyOCR', 'model')
            
            # Nếu đã có models trong user directory, bỏ qua
            if os.path.exists(user_models_dir):
                return
            
            # Copy models từ app directory vào user directory
            try:
                import shutil
                print("[INFO] Đang copy EasyOCR models từ app vào user directory...")
                os.makedirs(os.path.dirname(user_models_dir), exist_ok=True)
                shutil.copytree(app_models_dir, user_models_dir)
                print("[INFO] ✅ Đã copy EasyOCR models thành công!")
                print("[INFO] App sẽ không cần internet để sử dụng EasyOCR nữa.")
            except Exception as e:
                logging.error(f"Error copying EasyOCR models: {str(e)}")
        except Exception as e:
            logging.error(f"Error in _copy_easyocr_models_if_needed: {str(e)}")

    def _copy_paddleocr_models_if_needed(self):
        """Copy PaddleOCR models từ install directory vào user directory nếu chưa có"""
        if not USE_PADDLEOCR:
            return

        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))

            app_models_dir = os.path.join(app_dir, 'paddleocr_models')
            if not os.path.exists(app_models_dir):
                return

            user_home = os.path.expanduser('~')
            user_models_dir = os.path.join(user_home, '.paddleocr')

            if os.path.exists(user_models_dir):
                return

            try:
                import shutil
                print("[INFO] Đang copy PaddleOCR models từ app vào user directory...")
                os.makedirs(os.path.dirname(user_models_dir), exist_ok=True)
                shutil.copytree(app_models_dir, user_models_dir)
                print("[INFO] ✅ Đã copy PaddleOCR models thành công!")
                print("[INFO] App sẽ không cần internet để sử dụng PaddleOCR nữa.")
            except Exception as e:
                logging.error(f"Error copying PaddleOCR models: {str(e)}")
        except Exception as e:
            logging.error(f"Error in _copy_paddleocr_models_if_needed: {str(e)}")
    
    def _print_welcome(self):
        print("\n" + "="*60)
        print("  📷 CopyText App - Ứng dụng OCR chụp màn hình")
        print("="*60)
        print("\nCÁCH SỬ DỤNG:")
        print("  1. Click vào icon nổi (📷) ở góc màn hình")
        print("  2. Kéo chuột để chọn vùng muốn chụp")
        print("  3. Thả chuột để xử lý OCR")
        print("  4. Text sẽ tự động được copy vào clipboard")
        print("  5. Dán bằng Ctrl+V như bình thường")
        print("\nTÍNH NĂNG:")
        print("  • Hỗ trợ tiếng Việt và tiếng Anh")
        print("  • Tự động cải thiện chất lượng ảnh")
        print("  • Có thể kéo thả icon đến vị trí bất kỳ")
        print("  • Nhấn ESC hoặc click phải để hủy")
        print("\nLƯU Ý:")
        print("  • Lần đầu chạy có thể tải model OCR (nếu chưa có)")
        print("  • Đảm bảo vùng chọn có text rõ ràng để kết quả tốt nhất")
        print("\n" + "="*60)
        print("App đang chạy... Icon nổi sẽ xuất hiện ở góc màn hình\n")
        print("LƯU Ý: Vui lòng không đóng cửa sổ này để app hoạt động bình thường.\n")
    
    def _show_tooltip(self, canvas):
        if self.tooltip:
            self._hide_tooltip()
        
        x = self.root.winfo_x() + 70
        y = self.root.winfo_y() + 10
        
        self.tooltip = tk.Toplevel()
        self.tooltip.overrideredirect(True)
        self.tooltip.attributes('-topmost', True)
        self.tooltip.geometry(f'+{x}+{y}')
        
        label = tk.Label(
            self.tooltip,
            text="Click trái: Chụp màn hình\nClick phải: Menu\nDouble-click: Thoát\nKéo: Di chuyển",
            bg='#2C3E50',
            fg='white',
            font=('Arial', 9),
            padx=8,
            pady=5,
            relief=tk.SOLID,
            borderwidth=1
        )
        label.pack()
    
    def _hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def _show_context_menu(self, event):
        """Hiển thị menu khi click phải vào icon"""
        try:
            if self.context_menu:
                self.context_menu.destroy()
            
            self.context_menu = tk.Menu(self.root, tearoff=0)
            self.context_menu.add_command(label="📷 Chụp màn hình", command=self._capture_from_menu)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="❌ Thoát", command=self._on_closing)
            
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
        except Exception as e:
            logging.error(f"Error showing context menu: {str(e)}")
    
    def _on_double_click(self, event):
        """Đóng app khi double-click vào icon"""
        self._on_closing()
    
    def _capture_from_menu(self):
        """Chụp màn hình từ menu"""
        try:
            if self.context_menu:
                self.context_menu.destroy()
                self.context_menu = None
            self.root.withdraw()
            self.capture_screen()
        except Exception as e:
            logging.error(f"Error in _capture_from_menu: {str(e)}")
        
    def setup_icon(self):
        canvas = tk.Canvas(
            self.root, 
            width=60, 
            height=60, 
            bg='#2C3E50',
            highlightthickness=0
        )
        canvas.pack()
        
        canvas.create_oval(10, 10, 50, 50, fill='#3498DB', outline='#2980B9', width=2)
        canvas.create_text(30, 30, text='📷', font=('Arial', 20))
        
        canvas.bind('<Button-1>', self.on_click)
        canvas.bind('<B1-Motion>', self.on_drag)
        canvas.bind('<ButtonRelease-1>', self.on_release)
        canvas.bind('<Button-3>', self._show_context_menu)  # Click phải
        canvas.bind('<Double-Button-1>', self._on_double_click)  # Double click
        canvas.bind('<Enter>', lambda e: self._show_tooltip(canvas))
        canvas.bind('<Leave>', lambda e: self._hide_tooltip())
        
        self.tooltip = None
        self.context_menu = None
        
    def setup_bindings(self):
        self.start_x = 0
        self.start_y = 0
        self.dragging = False
        
    def on_click(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.root_start_x = self.root.winfo_x()
        self.root_start_y = self.root.winfo_y()
        self.dragging = False
        
    def on_drag(self, event):
        if not self.dragging:
            dx = abs(event.x_root - self.start_x)
            dy = abs(event.y_root - self.start_y)
            if dx > 5 or dy > 5:
                self.dragging = True
                
        if self.dragging:
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y
            x = self.root_start_x + dx
            y = self.root_start_y + dy
            self.root.geometry(f'+{x}+{y}')
            
    def on_release(self, event):
        if not self.dragging:
            self.root.withdraw()
            self.capture_screen()
        self.dragging = False
        
    def capture_screen(self):
        try:
            self.root.after(50, self.start_selection)
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi khi bắt đầu chụp màn hình: {str(e)}")
            self.root.deiconify()
            
    def _get_dpi_scale(self):
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            dc = user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)
            user32.ReleaseDC(0, dc)
            return dpi / 96.0
        except:
            return 1.0
    
    def _get_screen_size(self):
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            return width, height
        except:
            try:
                return self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            except:
                return 1920, 1080
    
    def start_selection(self):
        selection_window = None
        try:
            try:
                user32 = ctypes.windll.user32
                user32.SetProcessDPIAware()
                
                screen_width, screen_height = self._get_screen_size()
                
                selection_window = tk.Toplevel()
                selection_window.overrideredirect(True)
                selection_window.attributes('-topmost', True)
                selection_window.attributes('-alpha', 0.15)
                selection_window.configure(bg='black')
                selection_window.geometry(f'{screen_width}x{screen_height}+0+0')
                
                selection_window.update()
                selection_window.update_idletasks()
                selection_window.focus_force()
                
                canvas = tk.Canvas(
                    selection_window, 
                    highlightthickness=0,
                    cursor="crosshair",
                    bg='black'
                )
                canvas.pack(fill=tk.BOTH, expand=True)
                
                canvas.update()
                canvas.update_idletasks()
                
                start_x = start_y = 0
                rect_id = None
                size_text_id = None
                outer_rect = None
                inner_rect = None
                
                try:
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    if canvas_width <= 1:
                        canvas_width = screen_width
                    if canvas_height <= 1:
                        canvas_height = screen_height
                    
                    info_text = canvas.create_text(
                        canvas_width // 2, 30,
                        text="Kéo chuột để chọn vùng | ESC hoặc Click phải để hủy",
                        fill='white', font=('Arial', 11),
                        tags='info'
                    )
                except:
                    pass
                
                def on_press(event):
                    nonlocal start_x, start_y, rect_id, size_text_id, outer_rect, inner_rect
                    try:
                        start_x = event.x_root
                        start_y = event.y_root
                        if outer_rect:
                            try:
                                canvas.delete(outer_rect)
                            except:
                                pass
                        if rect_id:
                            try:
                                canvas.delete(rect_id)
                            except:
                                pass
                        if inner_rect:
                            try:
                                canvas.delete(inner_rect)
                            except:
                                pass
                        if size_text_id:
                            try:
                                canvas.delete(size_text_id)
                            except:
                                pass
                    except Exception as e:
                        logging.error(f"Error in on_press: {str(e)}")
                        
                def on_drag(event):
                    nonlocal rect_id, start_x, start_y, size_text_id, outer_rect, inner_rect
                    try:
                        current_x = event.x_root
                        current_y = event.y_root
                        
                        x1 = min(start_x, current_x)
                        y1 = min(start_y, current_y)
                        x2 = max(start_x, current_x)
                        y2 = max(start_y, current_y)
                        
                        width = x2 - x1
                        height = y2 - y1
                        
                        win_x = selection_window.winfo_x()
                        win_y = selection_window.winfo_y()
                        
                        canvas_x1 = x1 - win_x
                        canvas_y1 = y1 - win_y
                        canvas_x2 = x2 - win_x
                        canvas_y2 = y2 - win_y
                        
                        if outer_rect:
                            try:
                                canvas.delete(outer_rect)
                            except:
                                pass
                        if rect_id:
                            try:
                                canvas.delete(rect_id)
                            except:
                                pass
                        if inner_rect:
                            try:
                                canvas.delete(inner_rect)
                            except:
                                pass
                        if size_text_id:
                            try:
                                canvas.delete(size_text_id)
                            except:
                                pass
                        
                        try:
                            # Vẽ border đen bên ngoài để tạo viền nổi bật
                            outer_rect = canvas.create_rectangle(
                                canvas_x1 - 3, canvas_y1 - 3, canvas_x2 + 3, canvas_y2 + 3,
                                outline='#000000', width=4, fill=''
                            )
                            # Vẽ border vàng chính (nổi bật)
                            rect_id = canvas.create_rectangle(
                                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                                outline='#FFD700', width=5, fill='', stipple='gray50'
                            )
                            # Vẽ border đen bên trong để tăng độ tương phản
                            inner_rect = canvas.create_rectangle(
                                canvas_x1 + 2, canvas_y1 + 2, canvas_x2 - 2, canvas_y2 - 2,
                                outline='#000000', width=2, fill=''
                            )
                            
                            size_text = f"{int(width)} x {int(height)}"
                            size_text_id = canvas.create_text(
                                canvas_x1 + 5, canvas_y1 - 20,
                                text=size_text, fill='#FFD700', font=('Arial', 11, 'bold'),
                                anchor='nw', tags='size'
                            )
                        except:
                            pass
                    except Exception as e:
                        logging.error(f"Error in on_drag: {str(e)}")
                        
                def on_release(event):
                    nonlocal start_x, start_y
                    try:
                        end_x = event.x_root
                        end_y = event.y_root
                        
                        x1 = int(min(start_x, end_x))
                        y1 = int(min(start_y, end_y))
                        x2 = int(max(start_x, end_x))
                        y2 = int(max(start_y, end_y))
                        
                        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                            try:
                                selection_window.destroy()
                                selection_window.update()
                            except:
                                pass
                            
                            print(f"\n[INFO] Đang chụp vùng: ({x1}, {y1}) -> ({x2}, {y2})")
                            print(f"[INFO] Kích thước: {x2-x1} x {y2-y1} pixels")
                            
                            self.process_screenshot(x1, y1, x2, y2)
                        else:
                            try:
                                selection_window.destroy()
                            except:
                                pass
                            try:
                                self.root.deiconify()
                            except:
                                pass
                    except Exception as e:
                        logging.error(f"Error in on_release: {str(e)}")
                        try:
                            if selection_window:
                                selection_window.destroy()
                        except:
                            pass
                        try:
                            self.root.deiconify()
                        except:
                            pass
                    
                canvas.bind('<Button-1>', on_press)
                canvas.bind('<B1-Motion>', on_drag)
                canvas.bind('<ButtonRelease-1>', on_release)
                
                def cancel_selection(e=None):
                    try:
                        if selection_window:
                            selection_window.destroy()
                    except:
                        pass
                    try:
                        self.root.deiconify()
                    except:
                        pass
                    
                selection_window.bind('<Escape>', cancel_selection)
                selection_window.bind('<Button-3>', cancel_selection)
                
            except Exception as e:
                logging.error(f"Error creating selection window: {str(e)}\n{traceback.format_exc()}")
                try:
                    messagebox.showerror("Error", f"Lỗi khi chọn vùng: {str(e)}")
                except:
                    pass
                try:
                    self.root.deiconify()
                except:
                    pass
        except Exception as e:
            logging.error(f"Critical error in start_selection: {str(e)}\n{traceback.format_exc()}")
            try:
                if selection_window:
                    selection_window.destroy()
            except:
                pass
            try:
                self.root.deiconify()
            except:
                pass
            
    def _preload_easyocr(self):
        if not USE_EASYOCR or self.easyocr_ready or self.easyocr_loading:
            return
        
        self.easyocr_loading = True
        
        def load_in_thread():
            progress_window = None
            try:
                try:
                    progress_window = tk.Toplevel()
                    progress_window.title("Đang tải model...")
                    progress_window.geometry("450x200")
                    progress_window.attributes('-topmost', True)
                    progress_window.resizable(False, False)
                    
                    frame = tk.Frame(progress_window, padx=20, pady=20)
                    frame.pack(fill=tk.BOTH, expand=True)
                    
                    title = tk.Label(
                        frame,
                        text="Đang tải EasyOCR model...",
                        font=('Arial', 12, 'bold'),
                        fg='#3498DB'
                    )
                    title.pack(pady=10)
                    
                    info = tk.Label(
                        frame,
                        text="Lần đầu chạy sẽ tải model (khoảng 100MB).\nVui lòng chờ, không đóng app!",
                        font=('Arial', 10),
                        justify='center'
                    )
                    info.pack(pady=10)
                    
                    progress_var = tk.StringVar(value="Đang kiểm tra...")
                    progress_label = tk.Label(
                        frame,
                        textvariable=progress_var,
                        font=('Arial', 9),
                        fg='#7F8C8D'
                    )
                    progress_label.pack(pady=5)
                    
                    if progress_window:
                        progress_window.update()
                    
                    self.easyocr_reader = easyocr.Reader(['vi', 'en'], gpu=False, verbose=False)
                    
                    if progress_window:
                        progress_var.set("✅ Đã tải xong!")
                        progress_window.update()
                        progress_window.after(500, lambda: safe_call(progress_window.destroy) if progress_window else None)
                    
                    self.easyocr_ready = True
                    self.easyocr_loading = False
                    
                except Exception as e:
                    logging.error(f"Error loading EasyOCR: {str(e)}\n{traceback.format_exc()}")
                    if progress_window:
                        try:
                            progress_window.destroy()
                        except:
                            pass
                    self.easyocr_loading = False
                    self.easyocr_ready = False
            except Exception as e:
                logging.error(f"Critical error in EasyOCR thread: {str(e)}\n{traceback.format_exc()}")
                self.easyocr_loading = False
                self.easyocr_ready = False
        
        try:
            import threading
            thread = threading.Thread(target=load_in_thread, daemon=True)
            thread.start()
        except Exception as e:
            logging.error(f"Error starting EasyOCR thread: {str(e)}\n{traceback.format_exc()}")
            self.easyocr_loading = False
    
    def _preload_paddleocr(self):
        if not USE_PADDLEOCR or self.paddleocr_ready or self.paddleocr_loading:
            return

        self.paddleocr_loading = True

        def load_in_thread():
            progress_window = None
            try:
                try:
                    progress_window = tk.Toplevel()
                    progress_window.title("Đang tải model...")
                    progress_window.geometry("450x200")
                    progress_window.attributes('-topmost', True)
                    progress_window.resizable(False, False)

                    frame = tk.Frame(progress_window, padx=20, pady=20)
                    frame.pack(fill=tk.BOTH, expand=True)

                    title = tk.Label(
                        frame,
                        text="Đang tải PaddleOCR model...",
                        font=('Arial', 12, 'bold'),
                        fg='#3498DB'
                    )
                    title.pack(pady=10)

                    info = tk.Label(
                        frame,
                        text="Lần đầu chạy sẽ tải model OCR.\nVui lòng chờ, không đóng app!",
                        font=('Arial', 10),
                        justify='center'
                    )
                    info.pack(pady=10)

                    progress_var = tk.StringVar(value="Đang kiểm tra...")
                    progress_label = tk.Label(
                        frame,
                        textvariable=progress_var,
                        font=('Arial', 9),
                        fg='#7F8C8D'
                    )
                    progress_label.pack(pady=5)

                    if progress_window:
                        progress_window.update()

                    self.paddleocr_reader = PaddleOCR(
                        use_angle_cls=True,
                        lang='vi',
                        use_gpu=False,
                        show_log=False
                    )

                    if progress_window:
                        progress_var.set("✅ Đã tải xong!")
                        progress_window.update()
                        progress_window.after(500, lambda: safe_call(progress_window.destroy) if progress_window else None)

                    self.paddleocr_ready = True
                    self.paddleocr_loading = False

                except Exception as e:
                    logging.error(f"Error loading PaddleOCR: {str(e)}\n{traceback.format_exc()}")
                    if progress_window:
                        try:
                            progress_window.destroy()
                        except:
                            pass
                    self.paddleocr_loading = False
                    self.paddleocr_ready = False
            except Exception as e:
                logging.error(f"Critical error in PaddleOCR thread: {str(e)}\n{traceback.format_exc()}")
                self.paddleocr_loading = False
                self.paddleocr_ready = False

        try:
            import threading
            thread = threading.Thread(target=load_in_thread, daemon=True)
            thread.start()
        except Exception as e:
            logging.error(f"Error starting PaddleOCR thread: {str(e)}\n{traceback.format_exc()}")
            self.paddleocr_loading = False

    def _init_easyocr(self):
        if not USE_EASYOCR:
            return False
        
        if self.easyocr_ready and hasattr(self, 'easyocr_reader'):
            return True
        
        if self.easyocr_loading:
            messagebox.showinfo(
                "Đang tải model",
                "EasyOCR model đang được tải trong nền.\n"
                "Vui lòng chờ vài phút rồi thử lại!"
            )
            return False
        
        if not hasattr(self, 'easyocr_reader'):
            self._preload_easyocr()
            messagebox.showinfo(
                "Đang tải model",
                "EasyOCR model đang được tải.\n"
                "Vui lòng chờ vài phút rồi thử lại!"
            )
            return False
        
        return True

    def _init_paddleocr(self):
        if not USE_PADDLEOCR:
            return False

        if self.paddleocr_ready and hasattr(self, 'paddleocr_reader'):
            return True

        if self.paddleocr_loading:
            messagebox.showinfo(
                "Đang tải model",
                "PaddleOCR model đang được tải trong nền.\n"
                "Vui lòng chờ vài phút rồi thử lại!"
            )
            return False

        if not hasattr(self, 'paddleocr_reader'):
            self._preload_paddleocr()
            messagebox.showinfo(
                "Đang tải model",
                "PaddleOCR model đang được tải.\n"
                "Vui lòng chờ vài phút rồi thử lại!"
            )
            return False

        return True
    
    def _pil_to_numpy(self, pil_image):
        return np.array(pil_image)
    
    def _process_with_easyocr(self, screenshot):
        if not USE_EASYOCR:
            return None
        
        if not self.easyocr_ready or not hasattr(self, 'easyocr_reader'):
            return None
        
        try:
            if screenshot is None or screenshot.size[0] == 0 or screenshot.size[1] == 0:
                return None
            
            img_array = np.array(screenshot.convert('RGB'))
            if img_array.size == 0:
                return None
            
            results = self.easyocr_reader.readtext(img_array, paragraph=False)
            if results:
                text_items = []
                
                for result in results:
                    try:
                        if len(result) < 3:
                            continue
                        bbox, text, confidence = result[0], result[1], result[2]
                        if confidence < 0.5:
                            continue
                        
                        if not bbox or len(bbox) < 4:
                            continue
                        
                        if text and text.strip():
                            # Tính Y trung bình và X trung bình của bbox để sắp xếp
                            y_avg = sum(point[1] for point in bbox) / len(bbox)
                            x_avg = sum(point[0] for point in bbox) / len(bbox)
                            text_items.append((y_avg, x_avg, text.strip()))
                    except Exception as e:
                        logging.error(f"Error processing EasyOCR result: {str(e)}")
                        continue
                
                if text_items:
                    # Sắp xếp theo Y (từ trên xuống), sau đó theo X (từ trái sang phải)
                    # Làm tròn Y về bội số của 10 để nhóm các text cùng hàng
                    text_items.sort(key=lambda x: (round(x[0] / 10) * 10, x[1]))
                    texts = [item[2] for item in text_items]
                    # Nối tất cả text thành một dòng liên tục
                    result = ' '.join(texts)
                    # Loại bỏ các khoảng trắng thừa
                    result = ' '.join(result.split())
                    return result
                
                return None
        except Exception as e:
            logging.error(f"Error in EasyOCR processing: {str(e)}\n{traceback.format_exc()}")
            try:
                img_array = np.array(screenshot.convert('RGB'))
                if img_array.size > 0:
                    results = self.easyocr_reader.readtext(img_array, paragraph=False)
                    if results:
                        texts = []
                        for result in results:
                            try:
                                if len(result) >= 3 and result[2] >= 0.5:
                                    text = result[1].strip()
                                    if text:
                                        texts.append(text)
                            except:
                                continue
                        
                        if texts:
                            # Nối tất cả text thành một dòng liên tục
                            result = ' '.join(texts)
                            # Loại bỏ các khoảng trắng thừa
                            result = ' '.join(result.split())
                            return result
                        
                        return None
            except Exception as e2:
                logging.error(f"Error in EasyOCR fallback: {str(e2)}")
        return None

    def _process_with_paddleocr(self, screenshot):
        if not USE_PADDLEOCR:
            return None

        if not self.paddleocr_ready or not hasattr(self, 'paddleocr_reader'):
            return None

        try:
            if screenshot is None or screenshot.size[0] == 0 or screenshot.size[1] == 0:
                return None

            processed_img = self._preprocess_image(screenshot)
            img_array = np.array(processed_img.convert('RGB'))
            if img_array.size == 0:
                return None

            results = self.paddleocr_reader.ocr(img_array, cls=False)
            if not results:
                return None

            lines = results
            if len(results) == 1 and isinstance(results[0], list) and results[0] and len(results[0][0]) == 2:
                lines = results[0]

            text_items = []
            for line in lines:
                try:
                    if not line or len(line) < 2:
                        continue
                    bbox, text_info = line[0], line[1]
                    if not text_info or len(text_info) < 2:
                        continue
                    text, confidence = text_info[0], text_info[1]
                    if confidence < 0.5:
                        continue
                    if not bbox or len(bbox) < 4:
                        continue
                    if text and text.strip():
                        y_avg = sum(point[1] for point in bbox) / len(bbox)
                        x_avg = sum(point[0] for point in bbox) / len(bbox)
                        text_items.append((y_avg, x_avg, text.strip()))
                except Exception as e:
                    logging.error(f"Error processing PaddleOCR result: {str(e)}")
                    continue

            if text_items:
                text_items.sort(key=lambda x: (round(x[0] / 10) * 10, x[1]))
                texts = [item[2] for item in text_items]
                result = ' '.join(texts)
                result = ' '.join(result.split())
                return result

            return None
        except Exception as e:
            logging.error(f"Error in PaddleOCR processing: {str(e)}\n{traceback.format_exc()}")
        return None
    
    def _preprocess_image(self, image):
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # width, height = image.size
            # if width < 100 or height < 100:
            #     scale = max(300 / width, 300 / height)
            #     new_width = int(width * scale)
            #     new_height = int(height * scale)
            #     image = image.resize((new_width, new_height), Image.LANCZOS)
            # image = image.sized(width, height)
            
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
        except:
            return image
    
    def process_screenshot(self, x1, y1, x2, y2):
        try:
            try:
                bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                
                if bbox[2] - bbox[0] < 10 or bbox[3] - bbox[1] < 10:
                    try:
                        messagebox.showwarning("Cảnh báo", "Vùng chọn quá nhỏ!")
                    except:
                        pass
                    return
                
                if bbox[2] - bbox[0] > 5000 or bbox[3] - bbox[1] > 5000:
                    try:
                        messagebox.showwarning("Cảnh báo", "Vùng chọn quá lớn!")
                    except:
                        pass
                    return
                
                print(f"[INFO] Đang chụp màn hình với bbox: {bbox}")
                
                try:
                    screenshot = ImageGrab.grab(bbox=bbox, all_screens=False)
                except:
                    screenshot = ImageGrab.grab(bbox=bbox)
                
                actual_size = screenshot.size
                expected_width = bbox[2] - bbox[0]
                expected_height = bbox[3] - bbox[1]
                
                print(f"[INFO] Đã chụp xong")
                print(f"[INFO] Kích thước mong đợi: {expected_width} x {expected_height}")
                print(f"[INFO] Kích thước thực tế: {actual_size[0]} x {actual_size[1]}")
                
                if abs(actual_size[0] - expected_width) > 5 or abs(actual_size[1] - expected_height) > 5:
                    print(f"[WARNING] Kích thước không khớp! Có thể do DPI scaling.")
                    print(f"[WARNING] Thử điều chỉnh...")
                    
                    scale_x = expected_width / actual_size[0] if actual_size[0] > 0 else 1.0
                    scale_y = expected_height / actual_size[1] if actual_size[1] > 0 else 1.0
                    
                    if abs(scale_x - 1.0) > 0.1 or abs(scale_y - 1.0) > 0.1:
                        new_width = int(expected_width / scale_x) if scale_x > 0 else actual_size[0]
                        new_height = int(expected_height / scale_y) if scale_y > 0 else actual_size[1]
                        screenshot = screenshot.resize((new_width, new_height), Image.LANCZOS)
                        print(f"[INFO] Đã điều chỉnh kích thước: {screenshot.size}")
                
                if screenshot is None:
                    try:
                        messagebox.showerror("Error", "Không thể chụp màn hình!")
                    except:
                        pass
                    return
                
                if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                    try:
                        messagebox.showerror("Error", "Không thể chụp màn hình! Vùng chọn không hợp lệ.")
                    except:
                        pass
                    return
                
                text = None
                
                if USE_PADDLEOCR:
                    self._init_paddleocr()
                    try:
                        text = self._process_with_paddleocr(screenshot)
                    except Exception as e:
                        logging.error(f"Error in PaddleOCR: {str(e)}\n{traceback.format_exc()}")
                        text = None

                if not text and USE_EASYOCR:
                    try:
                        text = self._process_with_easyocr(screenshot)
                    except Exception as e:
                        logging.error(f"Error in EasyOCR: {str(e)}\n{traceback.format_exc()}")
                        text = None

                if not text and not USE_PADDLEOCR and not USE_EASYOCR:
                    try:
                        messagebox.showerror(
                            "Lỗi OCR",
                            "❌ Chưa có engine OCR nào!\n\n"
                            "Vui lòng cài đặt PaddleOCR hoặc EasyOCR:\n"
                            "- pip install paddleocr paddlepaddle\n"
                            "- pip install easyocr"
                        )
                    except:
                        pass
                
                if text and text.strip():
                    try:
                        pyperclip.copy(text)
                        char_count = len(text)
                        line_count = text.count('\n') + 1
                        preview = text[:100] + '...' if len(text) > 100 else text
                        
                        print(f"[SUCCESS] Đã copy {char_count} ký tự ({line_count} dòng) vào clipboard!")
                        print(f"[PREVIEW] {preview}")
                        print("[INFO] Bạn có thể dán bằng Ctrl+V\n")
                    except Exception as e:
                        logging.error(f"Error copying to clipboard: {str(e)}")
                        print(f"[ERROR] Không thể copy vào clipboard: {str(e)}")
                        try:
                            messagebox.showerror("Error", f"Không thể copy vào clipboard: {str(e)}")
                        except:
                            pass
                else:
                    print("[WARNING] Không tìm thấy text trong hình ảnh!")
                    try:
                        messagebox.showwarning("Cảnh báo", "Không tìm thấy text trong hình ảnh!")
                    except:
                        pass
                        
            except Exception as e:
                logging.error(f"Error in process_screenshot: {str(e)}\n{traceback.format_exc()}")
                try:
                    messagebox.showerror("Error", f"Lỗi khi xử lý ảnh: {str(e)}")
                except:
                    pass
        except Exception as e:
            logging.error(f"Critical error in process_screenshot: {str(e)}\n{traceback.format_exc()}")
            try:
                messagebox.showerror("Error", f"Lỗi nghiêm trọng: {str(e)}")
            except:
                pass
        finally:
            try:
                self.root.deiconify()
            except:
                pass
            
    def run(self):
        try:
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            logging.error(f"Error in mainloop: {str(e)}\n{traceback.format_exc()}")
            try:
                messagebox.showerror("Error", f"Lỗi nghiêm trọng: {str(e)}")
            except:
                pass
            sys.exit(1)
    
    def _on_closing(self):
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        sys.exit(0)

if __name__ == '__main__':
    try:
        if not USE_PADDLEOCR and not USE_EASYOCR:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Thiếu OCR",
                "⚠️ Chưa có engine OCR nào được cài!\n\n"
                "Vui lòng cài đặt PaddleOCR hoặc EasyOCR:\n"
                "- pip install paddleocr paddlepaddle\n"
                "- pip install easyocr"
            )
            root.destroy()
            sys.exit(0)

        app = FloatingIconApp()
        app.run()
    except Exception as e:
        try:
            messagebox.showerror("Error", f"Lỗi khởi động app: {str(e)}")
        except:
            print(f"Lỗi khởi động app: {str(e)}")

