import os
import sys
import threading
import time
import signal
from datetime import datetime
from block_manager import UsageManager, start_combined_loop

class ShutdownCUIApp:
    def __init__(self):
        self.running = True
        self.usage = UsageManager()
        
        # より多くのシグナルをキャッチ
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGUSR1, self.signal_handler)
        signal.signal(signal.SIGUSR2, self.signal_handler)
        
        print("🔒 === Shutdown Control App (保護モード) ===")
        print("⚠️  このアプリケーションはsudo権限でのみ終了できます")
        print("📍 終了方法: sudo pkill -f shutdown_cui.py")
        print("=" * 50)
        
        # 保護モード開始の通知
        self.notify_protection_start()
    
    def signal_handler(self, signum, frame):
        """シグナル受信時の処理 - sudo権限チェック"""
        print("\n⚠️  終了リクエストが検出されました")
        print("このアプリケーションはsudo権限でのみ終了できます。")
        
        # sudo権限のチェック
        if not self.check_sudo_permission():
            print("❌ sudo権限が必要です。終了が拒否されました。")
            print("終了するには: sudo pkill -f shutdown_cui.py")
            return
        
        print("✅ sudo権限が確認されました。アプリケーションを終了します...")
        self.running = False
    
    def check_sudo_permission(self):
        """sudo権限があるかチェック"""
        try:
            # sudoコマンドでID確認を試行
            import subprocess
            result = subprocess.run(
                ["sudo", "-n", "id"], 
                capture_output=True, 
                text=True, 
                timeout=1
            )
            return result.returncode == 0
        except:
            return False
    
    def notify_protection_start(self):
        """保護モード開始の通知"""
        try:
            import subprocess
            subprocess.run([
                "notify-send", 
                "--urgency=critical", 
                "🔒 デバイス使用制限開始",
                "保護モードが有効です。sudo権限でのみ終了可能。"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    
    def update_display(self):
        """時間表示の更新"""
        while self.running:
            sec = self.usage.seconds_left()
            mins = sec // 60
            rem_sec = sec % 60
            hours = mins // 60
            rem_mins = mins % 60
            
            # カーソルを行の先頭に戻して上書き
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_line = f"\r[{timestamp}] 残り使用可能時間: {hours:02d}:{rem_mins:02d}:{rem_sec:02d}"
            print(status_line, end="", flush=True)
            
            time.sleep(1)
    
    def run(self):
        """メインループ - 保護モード"""
        try:
            # バックグラウンドで時間管理スレッドを開始
            control_thread = threading.Thread(target=start_combined_loop, daemon=True)
            control_thread.start()
            
            # 表示更新スレッドを開始
            display_thread = threading.Thread(target=self.update_display, daemon=True)
            display_thread.start()
            
            # メインスレッドは保護モードで待機
            consecutive_interrupts = 0
            while self.running:
                try:
                    time.sleep(0.1)
                    consecutive_interrupts = 0  # 正常に実行できればリセット
                except KeyboardInterrupt:
                    consecutive_interrupts += 1
                    print(f"\n🚫 終了試行が検出されました (試行回数: {consecutive_interrupts})")
                    print("sudo権限が必要です。強制終了は無視されます。")
                    if consecutive_interrupts >= 5:
                        print("⚠️  複数回の終了試行が検出されました。管理者に通知します。")
                        self.notify_tampering_attempt()
                        consecutive_interrupts = 0
                    continue
                    
        except Exception as e:
            print(f"\n❌ 予期しないエラー: {e}")
            print("保護モードを維持します...")
            # エラーが発生しても終了しない
            time.sleep(1)
            if self.running:
                print("🔄 アプリケーションを再起動します...")
                self.run()  # 再帰的に再起動
        finally:
            if self.running:
                print("\n🔒 保護モードが維持されています。")
            else:
                print("\n✅ 正常に終了しました。")
    
    def notify_tampering_attempt(self):
        """改ざん試行の通知"""
        try:
            import subprocess
            subprocess.run([
                "notify-send", 
                "--urgency=critical", 
                "🚨 セキュリティ警告",
                "不正な終了試行が検出されました。管理者に報告されます。"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

if __name__ == "__main__":
    app = ShutdownCUIApp()
    app.run()
