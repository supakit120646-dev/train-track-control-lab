import tkinter as tk
import datetime

# คลาสสำหรับเก็บข้อมูลพิกัด (x, y) ของแต่ละช่อง
class Tile:
    def __init__(self, x, y):
        self.x = x  # พิกัดแกน X
        self.y = y  # พิกัดแกน Y

# คลาสหลักที่จัดการตรรกะการจำลองทั้งหมด (State, Train, Paths)
class TrainSimulator:
    
    # ฟังก์ชันเริ่มต้น (Constructor) ของคลาส
    def __init__(self, canvas, screen_width, screen_height, logger_callback):
        """
        ตั้งค่าเริ่มต้นทั้งหมดสำหรับ Simulator
        - canvas: พื้นที่วาดรูปของ tkinter
        - screen_width, screen_height: ขนาดหน้าจอ
        - logger_callback: ฟังก์ชันสำหรับส่งข้อความกลับไปแสดงใน Log ของ GUI
        """
        
        self.canvas = canvas
        # 'ts' (Tile Size) คำนวณขนาดของไทล์แต่ละช่อง เทียบกับความกว้างหน้าจอ
        self.ts = screen_width / 125.0  
        self.train_length = 17  # ความยาวของรถไฟ (จำนวนไทล์)
        self.log = logger_callback  # เก็บฟังก์ชัน log ไว้ใช้งาน
        
        # --- คำนวณเลย์เอาต์ของสถานี ---
        total_tile_width = 125  # ความกว้างทั้งหมดของแผนที่ (จำนวนไทล์)
        
        # กำหนดขนาดของส่วนต่างๆ ในสถานี
        diag_len = 10      # ความยาวของส่วนทางเบี่ยง (เฉียง)
        horiz_len = 25     # ความยาวของส่วนชานชาลา (ตรง)
        # ความกว้างรวมของสถานี (เบี่ยงขึ้น + ตรง + เบี่ยงลง)
        station_width_tiles = diag_len + horiz_len + diag_len
        
        # คำนวณจุด  เริ่มต้นของสถานี 
        station_start_x = (total_tile_width // 2) - (station_width_tiles // 2) + 1
        
        diag_y_start = 40  # พิกัด y เริ่มต้นของทางหลัก (ก่อนเบี่ยง)
        
        # --- สร้างรายการพิกัด (List of Tile) สำหรับเส้นทางต่างๆ ---
        
        # 1. เส้นทางเบี่ยงขึ้น (ชานชาลาบน)
        self.path_top_diag_up = [Tile((station_start_x + i) * self.ts, (diag_y_start - i) * self.ts) for i in range(diag_len + 1)]
        
        # 2. เส้นทางตรง (ชานชาลาบน)
        horiz_start_x = station_start_x + diag_len
        station_top_y = diag_y_start - diag_len
        self.path_top_horizontal = [Tile(x * self.ts, station_top_y * self.ts) for x in range(horiz_start_x, horiz_start_x + horiz_len)]

        # 3. เส้นทางเบี่ยงลง (ชานชาลาบน)
        diag_down_start_x = horiz_start_x + horiz_len
        self.path_top_diag_down = [Tile((diag_down_start_x + i) * self.ts, (station_top_y + i) * self.ts) for i in range(diag_len + 1)]
        
        # 4. เส้นทางหลัก (ก่อนเข้าสถานี)
        station_end_x = diag_down_start_x + diag_len
        self.path_main = [Tile(i * self.ts, 40 * self.ts) for i in range(station_start_x)]
        
        # 5. เส้นทางกลาง (ชานชาลาล่าง)
        self.path_middle = [Tile(i * self.ts, 40 * self.ts) for i in range(station_start_x, station_end_x + 1)]
        
        # 6. เส้นทางออกหลัก (หลังออกจากสถานี)
        self.path_end = [Tile(i * self.ts, 40 * self.ts) for i in range(station_end_x + 1, int(125 + self.train_length))]
        
        
        # --- รวมเส้นทางย่อยเป็นเส้นทางเต็ม (ขาเข้า) ---
        # เส้นทางที่ 1 (บน): ทางหลัก + เบี่ยงขึ้น + ชานชาลาบน + เบี่ยงลง + เส้นทางออกหลัก
        self.path_top_station = (
            self.path_main + self.path_top_diag_up + 
            self.path_top_horizontal + self.path_top_diag_down
        )
        # เส้นทางที่ 2 (ล่าง): ทางหลัก + ชานชาลาล่าง + เส้นทางออกหลัก
        self.path_bottom_station = self.path_main + self.path_middle
        
        
        # --- ตัวแปรสถานะ (State) ของ Simulator ---
        self.train_path = []  # เส้นทางที่รถไฟขบวนปัจจุบันกำลังวิ่ง
        self.train_index = 0  # ตำแหน่ง (index) ปัจจุบันของหัวรถไฟใน train_path
        self.train_positions = []  # รายการพิกัด (Tile) ที่ตัวรถไฟทั้งหมดครอบครอง
        self.train_rects = [] 
        
        self.state = "ready"  # สถานะปัจจุบัน: ready, running, in_station, leaving, emergency
        self.use_top_station = True  # เก็บว่าเส้นทางที่ตั้งไว้ใช้ชานชาลาบนหรือไม่
        self.last_platform = 0  # เก็บหมายเลขชานชาลาล่าสุดที่ใช้งาน
        
        self.platform_occupied = {1: False, 2: False} # สถานะว่าชานชาลาว่างหรือไม่
        self.route_locked = None  # สถานะการล็อกเส้นทาง (เช่น "P1_IN", "P2_OUT")
        
        self.station_stop_index = 0 # ตำแหน่ง (index) ใน path ที่รถไฟต้องหยุด (คำนวณใน set_route_in)
        
        
        self.train_id_counter = 100  # ตัวนับ ID รถไฟ
        self.current_train_id = None  # ID ของรถไฟขบวนปัจจุบัน
        
        
        self.log("[SIM] Simulator initialized.")

        
        # --- วาดส่วน Track ที่แสดงสถานะ Occupancy (ทับเส้นทางพื้นฐาน) ---
        self.track_width = max(2, self.ts / 2.5) # ความหนาของเส้น Track
        
        # สร้างเส้นสำหรับชานชาลา 1 (บน)
        p1_coords = []
        for tile in self.path_top_horizontal:
            p1_coords.extend([tile.x + self.ts / 2, tile.y + self.ts / 2])
        self.track_p1_id = self.canvas.create_line(p1_coords, fill="gray", width=self.track_width, tags="track_platform")

        # สร้างเส้นสำหรับชานชาลา 2 (ล่าง)
        p2_coords = []
        for tile in self.path_middle:
            # วาดเฉพาะส่วนที่ตรงกับชานชาลาบน (เพื่อความสวยงาม)
            if tile.x >= horiz_start_x * self.ts and tile.x < diag_down_start_x * self.ts:
                p2_coords.extend([tile.x + self.ts / 2, tile.y + self.ts / 2])
        self.track_p2_id = self.canvas.create_line(p2_coords, fill="gray", width=self.track_width, tags="track_platform")
        self.log("[SIM] Platform occupancy segments created.")


    def draw_base_tracks(self):
        """วาดเส้นทางรถไฟพื้นฐาน (สีเทา) ทั้งหมด"""
        self.canvas.delete("track_base")  # ลบของเก่า
        track_color = "gray"
        
        # 1. วาดเส้นทางหลักด้านล่าง (เส้นเต็ม)
        bottom_track_path = self.path_main + self.path_middle + self.path_end
        bottom_coords = []
        for tile in bottom_track_path:
            bottom_coords.extend([tile.x + self.ts / 2, tile.y + self.ts / 2])
        self.canvas.create_line(bottom_coords, fill=track_color, width=self.track_width, tags="track_base")

        # 2. วาดเส้นทางเบี่ยง (ส่วนโค้ง)
        top_track_path = self.path_top_diag_up + self.path_top_diag_down
        top_coords = []
        for tile in top_track_path:
            top_coords.extend([tile.x + self.ts / 2, tile.y + self.ts / 2])
        self.canvas.create_line(top_coords, fill=track_color, width=self.track_width, tags="track_base")
        
        # 3. ย้ายเส้นชานชาลา (track_p1, track_p2) มาไว้ข้างหน้าสุด
        self.canvas.tag_raise(self.track_p1_id)
        self.canvas.tag_raise(self.track_p2_id)


    def draw_train(self):
        """วาดตัวรถไฟ (ตามพิกัดใน self.train_positions)"""
        self.canvas.delete("train")  # ลบรถไฟเก่า
        self.train_rects.clear()

        # ถ้าไม่มีพิกัดรถไฟ ก็ไม่ต้องวาด
        if not self.train_positions:
            return
        
        # กำหนดสีรถไฟตามสถานะ
        train_color = "#4ade80"  # สีเขียว (จอด)
        if self.state == "running" or self.state == "leaving":
            train_color = "#f87171"  # สีแดง (กำลังวิ่ง)

        # แปลงรายการ Tile เป็นรายการพิกัด (x, y, x, y, ...)
        train_coords = []
        for pos in self.train_positions:
            train_coords.extend([pos.x + self.ts / 2, pos.y + self.ts / 2])
        
        # วาดรถไฟเป็นเส้นหนา (ถ้ามีความยาวมากกว่า 1)
        if len(self.train_positions) > 1:
            self.canvas.create_line(
                train_coords, fill=train_color, width=self.ts,
                capstyle=tk.ROUND, joinstyle=tk.ROUND, tags="train"
            )


    def set_route_in(self, platform):
        """ตั้งค่าเส้นทางสำหรับรถไฟขาเข้า (INBOUND)"""
        
        # ตรวจสอบว่าระบบล็อกอยู่หรือไม่
        if self.route_locked:
            self.log(f"[ERROR] Cannot set route: System is locked ({self.route_locked}).")
            return
        # ตรวจสอบว่าชานชาลาว่างหรือไม่
        if self.platform_occupied[platform]:
            self.log(f"[ERROR] Cannot set route: Platform {platform} is occupied.")
            return

        # ตั้งค่าตัวแปรสำหรับเส้นทางนี้
        self.use_top_station = (platform == 1)
        self.last_platform = platform
        self.route_locked = f"P{platform}_IN"  # ล็อกระบบสำหรับขาเข้า
        
        # คำนวณจุดหยุดรถไฟ 
        # จุดหยุด = กึ่งกลางของชานชาลา + ครึ่งหนึ่งของความยาวรถไฟ
        half_train = self.train_length // 2
        if self.use_top_station:
            # (ทางหลัก + ทางเบี่ยงขึ้น) + (ครึ่งชานชาลาบน) + ครึ่งขบวน
            self.station_stop_index = len(self.path_main) + len(self.path_top_diag_up) + (len(self.path_top_horizontal) // 2) + half_train
        else:
            # (ทางหลัก) + (ครึ่งชานชาลากลาง) + ครึ่งขบวน
            self.station_stop_index = len(self.path_main) + (len(self.path_middle) // 2) + half_train
        
        self.log(f"[SYS] Route set: INBOUND to Platform {platform}. System locked.")
        

    def set_route_out(self, platform):
        """ตั้งค่าเส้นทางสำหรับรถไฟขาออก (OUTBOUND)"""
        
        # ตรวจสอบเงื่อนไขต่างๆ
        if self.route_locked:
            self.log(f"[ERROR] Cannot set route: System is locked ({self.route_locked}).")
            return
        if not self.platform_occupied[platform]:
            self.log(f"[ERROR] Cannot depart: Platform {platform} is empty.")
            return
        if self.state != "in_station":
            self.log(f"[ERROR] Cannot depart: Train not in station.")
            return
        
        # ล็อกเส้นทาง
        self.route_locked = f"P{platform}_OUT"
        self.log(f"[SYS] Route set: OUTBOUND from Platform {platform}. System locked.")
        
        # สั่งให้รถไฟเริ่มเคลื่อนที่ (ฟังก์ชันนี้จะถูกเรียกจาก _move_train)
        self.release_train()

    def call_train(self):
        """
        'เรียก' รถไฟขบวนใหม่เข้ามาในระบบ (เริ่มจำลองการเคลื่อนที่ขาเข้า)
        """
        if self.state != "ready": return  # ต้องอยู่ในสถานะพร้อม
        # ต้องมีเส้นทางขาเข้า (IN) ตั้งค่าไว้แล้ว
        if not self.route_locked or not self.route_locked.endswith("_IN"):
            self.log(f"[ERROR] Cannot arrive: No inbound route set.")
            return

        # สร้าง ID รถไฟใหม่
        self.current_train_id = f"ขบวนที่ {self.train_id_counter}"
        self.train_id_counter += 1
        
        # เลือกเส้นทาง (path) ตามที่ตั้งค่าไว้ (บนหรือล่าง)
        self.train_path = self.path_top_station if self.use_top_station else self.path_bottom_station
        self.train_index = 0
        self.train_positions.clear()
        
        # เปลี่ยนสถานะเป็น "กำลังวิ่ง"
        self.state = "running"
        self.log(f"[TRAIN] {self.current_train_id} arriving on route {self.route_locked}.")
        
        # เริ่มการเคลื่อนที่ครั้งแรก
        self._move_train()

    def release_train(self):
        """
        เตรียมการและเริ่มการเคลื่อนที่ขาออก
        """
        
        # ตรวจสอบว่าอยู่ในสถานะจอด และตั้งเส้นทางขาออก (OUT) แล้ว
        if self.state != "in_station" or not self.route_locked.endswith("_OUT"):
             self.log(f"[ERROR] Release train failed. State: {self.state}, Route: {self.route_locked}")
             return
        
        self.log(f"[TRAIN] {self.current_train_id} departing from Platform {self.last_platform}.")
        
        # --- คำนวณเส้นทางที่เหลือ (สำคัญ) ---
        
        # 1. หาพิกัดหัวรถไฟปัจจุบัน
        current_head = self.train_positions[-1] 
        
        # 2. กำหนด path ส่วนที่รถไฟจอดอยู่
        start_path_segment = (self.path_top_horizontal + self.path_top_diag_down) if self.use_top_station else self.path_middle
        
        try:
            # 3. หาว่าหัวรถไฟอยู่ index ที่เท่าไหร่ใน path ส่วนนั้น
            current_path_index = -1
            for i, tile in enumerate(start_path_segment):
                if tile.x == current_head.x and tile.y == current_head.y:
                    current_path_index = i
                    break
            
            # 4. สร้าง train_path ใหม่ = ส่วนที่เหลือของ path เดิม + path_end
            if current_path_index != -1:
                self.train_path = (start_path_segment[current_path_index:] + self.path_end)
            else:
                # ถ้าหาไม่เจอ (เกิดข้อผิดพลาด) ให้ใช้ path_end ไปเลย
                self.train_path = self.path_end
        except IndexError:
            self.train_path = self.path_end
            
        # 5. รีเซ็ต index และตั้งสถานะ "กำลังออก"
        self.train_index = 0
        self.state = "leaving"
        
        # เริ่มการเคลื่อนที่
        self._move_train()

    def emergency_stop(self):
        """หยุดฉุกเฉิน - เคลียร์ทุกอย่างและรีเซ็ต"""
        self.log("[!!EMERGENCY!!] All signals RED. Train movement halted.")
        
        self.state = "emergency"  # ตั้งสถานะฉุกเฉิน (เพื่อหยุด _move_train)
        self.route_locked = "EMERGENCY" # ล็อกระบบ
        
        # เคลียร์รถไฟและสถานะชานชาลา
        self.canvas.delete("train")
        self.train_positions.clear()
        self.platform_occupied = {1: False, 2: False}
        self.current_train_id = None
        
        # รีเซ็ตสี Track ชานชาลา
        self.canvas.itemconfig(self.track_p1_id, fill="gray")
        self.canvas.itemconfig(self.track_p2_id, fill="gray")
        
        # หน่วงเวลา 2 วินาที แล้วค่อยเรียกฟังก์ชันรีเซ็ต
        self.canvas.after(2000, self.reset_from_emergency)
        
    def reset_from_emergency(self):
        """รีเซ็ตสถานะกลับเป็น 'พร้อม' หลังจากหยุดฉุกเฉิน"""
        self.log("[SYS] System resetting from emergency.")
        self.state = "ready"
        self.route_locked = None

    def _move_train(self):
        """
        ฟังก์ชันหลักที่ขับเคลื่อนรถไฟ (Loop)
        จะเรียกตัวเองซ้ำๆ ผ่าน self.canvas.after()
        """
        
        # ถ้าอยู่ในสถานะฉุกเฉิน ให้หยุดทันที
        if self.state == "emergency":
            self.log("[TRAIN] Movement halted by emergency stop.")
            return

        delay_ms = 70  # ความเร็วรถไฟ (ยิ่งน้อยยิ่งเร็ว)

        # --- ส่วนที่ 1: รถไฟยังมีเส้นทางเหลือให้วิ่ง (เพิ่มหัว) ---
        if self.train_index < len(self.train_path):
            # 1. เอาพิกัดถัดไป (หัวรถไฟ)
            head = self.train_path[self.train_index]
            self.train_positions.append(head)
            
            # 2. ถ้าขบวนยาวเกิน ให้ลบหาง (pop 0)
            if len(self.train_positions) > self.train_length: 
                self.train_positions.pop(0)
            
            # 3. วาดรถไฟ
            self.draw_train()
            
            # 4. ตรวจสอบว่าถึงจุดหยุด (สำหรับขาเข้า) หรือยัง
            if self.state == "running" and self.train_index >= self.station_stop_index:
                self.state = "in_station"  # เปลี่ยนสถานะเป็น "จอดในสถานี"
                self.route_locked = None   # ปลดล็อกเส้นทาง
                self.platform_occupied[self.last_platform] = True # ตั้งค่าว่าชานชาลาไม่ว่าง
                
                # เปลี่ยนสี Track ชานชาลา (ในโค้ดนี้คือเปลี่ยนกลับเป็นสีเทา)
                platform_track_id = self.track_p1_id if self.last_platform == 1 else self.track_p2_id
                self.canvas.itemconfig(platform_track_id, fill="gray") # (อาจเปลี่ยนเป็นสีแดง/ส้ม เพื่อโชว์ว่า occupied)
                
                self.log(f"[TRAIN] {self.current_train_id} at Platform {self.last_platform}. Route unlocked.")
                self.draw_train()  # วาดซ้ำ (อาจเปลี่ยนสี)
                return  # หยุด Loop (รอคำสั่งใหม่)
                
            # 5. ถ้ายังไม่ถึงจุดหยุด ให้เลื่อน index และเรียกตัวเองใหม่
            self.train_index += 1
            self.canvas.after(delay_ms, self._move_train)
            
        # --- ส่วนที่ 2: รถไฟวิ่งเลยเส้นทางแล้ว (ลบหาง) ---
        elif self.train_positions:
            # 1. รถไฟวิ่งพ้น path แล้ว แต่ตัวขบวนยังค้างอยู่
            # 2. ลบหาง (pop 0) จนกว่าขบวนจะหายไปหมด
            self.train_positions.pop(0)
            self.draw_train()
            self.canvas.after(delay_ms, self._move_train)
            
        # --- ส่วนที่ 3: รถไฟออกจากแผนที่ไปหมดแล้ว ---
        else:
            # 1. รถไฟหายไปหมดแล้ว (สำหรับขาออก)
            self.log(f"[TRAIN] {self.current_train_id} has left Platform {self.last_platform}. Map clear.")
            self.state = "ready"  # สถานะพร้อม
            self.route_locked = None  # ปลดล็อก
            self.platform_occupied[self.last_platform] = False # ชานชาลาว่าง
            self.current_train_id = None
            
            # 2. รีเซ็ตสี Track ชานชาลา
            platform_track_id = self.track_p1_id if self.last_platform == 1 else self.track_p2_id
            self.canvas.itemconfig(platform_track_id, fill="gray")
            
            # 3. ลบรถไฟ (เผื่อค้าง)
            self.canvas.delete("train")
            self.train_path, self.train_index, self.train_positions = [], 0, [] # รีเซ็ตตัวแปร

# คลาสที่จัดการหน้าจอ GUI (ปุ่ม, หน้าต่าง, Log)
class TrainApp:
    def __init__(self, root):
        """
        ตั้งค่าหน้าต่างโปรแกรม (GUI) ทั้งหมด
        - root: หน้าต่างหลักของ tkinter
        """
        self.root = root
        self.root.title("🚉 ระบบควบคุมสถานีรถไฟ (Interlocking)")
        self.root.attributes('-fullscreen', True)  # เต็มจอ
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # --- สร้าง Frame หลัก ---
        self.main_frame = tk.Frame(root, bg="black")
        self.main_frame.pack(fill="both", expand=True)

        # 1. Canvas (ส่วนวาดรูป)
        self.canvas = tk.Canvas(self.main_frame, width=self.screen_width, height=self.screen_height * 0.85, bg="black", borderwidth=0, highlightthickness=0)
        self.canvas.pack(side="top", fill="x")

        # 2. Log Frame (ส่วนแสดงข้อความ)
        log_frame_height = self.screen_height * 0.15
        self.log_frame = tk.Frame(self.main_frame, height=log_frame_height, bg="#111")
        self.log_frame.pack(side="bottom", fill="x")
        self.log_frame.pack_propagate(False)  # กัน Frame หดตัว

        # สร้าง Text widget และ Scrollbar สำหรับ Log
        log_scroll = tk.Scrollbar(self.log_frame, orient="vertical")
        self.log_text = tk.Text(self.log_frame, bg="#111", fg="white", font=("Arial", 10),
                                  wrap="word", yscrollcommand=log_scroll.set, state="disabled",
                                  borderwidth=0, highlightthickness=0)
        log_scroll.config(command=self.log_text.yview)
        
        log_scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        self.log_message("[APP] Application started. Welcome, controller.")
        
        # --- สร้าง Simulator ---
        # ส่ง canvas และฟังก์ชัน log_message ไปให้ Simulator ใช้งาน
        self.sim = TrainSimulator(self.canvas, self.screen_width, self.screen_height, self.log_message)
        
        # ผูกปุ่ม Escape เพื่อออกจากโหมดเต็มจอ
        self.root.bind("<Escape>", self.close_fullscreen)
        
        # --- วาดองค์ประกอบ UI ลงบน Canvas ---
        ts = self.sim.ts
        signal_radius = ts * 0.5
        
        # สัญญาณ S-01 (Home Signal)
        s1_tile_x = len(self.sim.path_main) - 10  # พิกัด x
        s1_x, s1_y = ts * s1_tile_x, ts * 42  # พิกัด y (เยื้องลงมา)
        self.signal_1 = self.canvas.create_oval(s1_x - signal_radius, s1_y - signal_radius, s1_x + signal_radius, s1_y + signal_radius, fill="red", outline="", tags="signal")
        self.canvas.create_text(s1_x, s1_y + ts * 1.5, text="S-01 (Home)", fill="white", font=("Arial", 9), tags="label")

        # สัญญาณ S-P1 (Departure P1)
        p1_tile_x = self.sim.path_top_horizontal[0].x / ts + 2 # พิกัด x (ต้นชานชาลา)
        p1_x, p1_y = ts * p1_tile_x, self.sim.path_top_horizontal[0].y - ts * 1.5 # พิกัด y (เยื้องขึ้น)
        self.signal_p1_depart = self.canvas.create_oval(p1_x - signal_radius, p1_y - signal_radius, p1_x + signal_radius, p1_y + signal_radius, fill="red", outline="", tags="signal")
        self.canvas.create_text(p1_x, p1_y - ts, text="S-P1", fill="white", font=("Arial", 9), tags="label")
        self.canvas.create_text(p1_x + ts * 10, p1_y, text="ชานชาลา 1 (บน)", fill="white", font=("Arial", 11), tags="label")

        # สัญญาณ S-P2 (Departure P2)
        p2_tile_x = self.sim.path_middle[0].x / ts + 2 # พิกัด x (ต้นชานชาลา)
        p2_x, p2_y = ts * p2_tile_x, self.sim.path_middle[0].y + ts * 1.5 # พิกัด y (เยื้องลง)
        self.signal_p2_depart = self.canvas.create_oval(p2_x - signal_radius, p2_y - signal_radius, p2_x + signal_radius, p2_y + signal_radius, fill="red", outline="", tags="signal")
        self.canvas.create_text(p2_x, p2_y + ts, text="S-P2", fill="white", font=("Arial", 9), tags="label")
        self.canvas.create_text(p2_x + ts * 20, p2_y, text="ชานชาลา 2 (ล่าง)", fill="white", font=("Arial", 11), tags="label")

        # สัญญาณ S-03 (Starter Signal)
        s3_tile_x = len(self.sim.path_main) + len(self.sim.path_middle) + 5 # พิกัด x (หลังสถานี)
        s3_x, s3_y = ts * s3_tile_x, ts * 42 # พิกัด y (เยื้องลง)
        self.signal_3 = self.canvas.create_oval(s3_x - signal_radius, s3_y - signal_radius, s3_x + signal_radius, s3_y + signal_radius, fill="red", outline="", tags="signal")
        self.canvas.create_text(s3_x, s3_y + ts * 1.5, text="S-03 (Starter)", fill="white", font=("Arial", 9), tags="label")
        
        # --- ป้ายชื่อและสถานะ ---
        self.status_label = tk.Label(self.canvas, text="สถานะ: พร้อม",bg="black", font=("Arial", 12, "bold"), fg="green")
        self.canvas.create_window(self.screen_width / 2, self.screen_height * 0.73, window=self.status_label)
        
        self.station_name_label = tk.Label(self.canvas, text="สถานีรถไฟปากน้ำ",bg="black", font=("Arial", 36, "bold"), fg="cyan")
        self.canvas.create_window(self.screen_width / 2, self.screen_height * 0.1, window=self.station_name_label)
        
        self.clock_label = tk.Label(self.canvas, text="", bg="black", font=("Arial", 18, "bold"), fg="white")
        self.canvas.create_window(self.screen_width / 2, self.screen_height * 0.1 + 50, window=self.clock_label)
        
        
        # --- สร้างปุ่มควบคุม ---
        btn_y_pos = self.screen_height * 0.78 # ตำแหน่ง Y ของปุ่ม
        btn_font = ("Arial", 10, "bold")
        
        # ปุ่มตั้งเส้นทางเข้า (Inbound)
        self.btn_route_p1 = tk.Button(self.canvas, text="เส้นทางเข้า P1 (บน)", width=20, command=lambda: self.handle_route_in(1), font=btn_font, relief="raised", bg="#c7d2fe", fg="black")
        self.btn_route_p2 = tk.Button(self.canvas, text="เส้นทางเข้า P2 (ล่าง)", width=20, command=lambda: self.handle_route_in(2), font=btn_font, relief="raised", bg="#c7d2fe", fg="black")
        
        # ปุ่มเรียกรถไฟ (Arrive)
        self.btn_arrive = tk.Button(self.canvas, text="รถไฟเข้า", width=20, command=self.handle_arrive, font=btn_font, relief="raised", bg="#fef08a", fg="black", state="disabled")
        
        # ปุ่มตั้งเส้นทางออก (Outbound)
        self.btn_depart_p1 = tk.Button(self.canvas, text="ออกเส้นทาง P1", width=20, command=lambda: self.handle_route_out(1), font=btn_font, relief="raised", bg="#bbf7d0", fg="black", state="disabled")
        self.btn_depart_p2 = tk.Button(self.canvas, text="ออกเส้นทาง P2", width=20, command=lambda: self.handle_route_out(2), font=btn_font, relief="raised", bg="#bbf7d0", fg="black", state="disabled")
        
        # ปุ่มหยุดฉุกเฉิน
        self.btn_emergency = tk.Button(self.canvas, text="!! หยุดฉุกเฉิน !!", width=20, command=self.handle_emergency, font=btn_font, relief="raised", bg="#dc2626", fg="white")

        # --- จัดวางปุ่มลงบน Canvas ---
        self.canvas.create_window(self.screen_width * 0.35, btn_y_pos, window=self.btn_route_p1)
        self.canvas.create_window(self.screen_width * 0.35, btn_y_pos + 40, window=self.btn_route_p2)
        
        self.canvas.create_window(self.screen_width * 0.5, btn_y_pos, window=self.btn_arrive)
        
        self.canvas.create_window(self.screen_width * 0.65, btn_y_pos, window=self.btn_depart_p1)
        self.canvas.create_window(self.screen_width * 0.65, btn_y_pos + 40, window=self.btn_depart_p2)
        
        self.canvas.create_window(self.screen_width * 0.5, btn_y_pos + 40, window=self.btn_emergency)
        
        # --- เริ่มการทำงาน ---
        self.sim.draw_base_tracks() # วาด Track ครั้งแรก
        self._update_time()         # เริ่ม Loop นาฬิกา
        self._monitor()             # เริ่ม Loop ตรวจสอบสถานะ (UI update)

    def log_message(self, msg):
        """เพิ่มข้อความลงในกล่อง Log (Text widget)"""
        try:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"[{now}] {msg}\n"
            
            self.log_text.config(state="normal")  # เปิดให้แก้ไข
            self.log_text.insert(tk.END, formatted_msg) # เพิ่มข้อความ
            self.log_text.see(tk.END)  # เลื่อนไปล่างสุด
            self.log_text.config(state="disabled") # ปิดการแก้ไข
        except Exception as e:
            print(f"Log Error: {e}")  # พิมพ์ error ถ้า GUI พัง

    def close_fullscreen(self, event=None):
        """ออกจากโหมดเต็มจอ (เมื่อกด Escape)"""
        self.log_message("[APP] Closing fullscreen.")
        self.root.attributes('-fullscreen', False)

    
    def _update_time(self):
        """อัปเดตนาฬิกา (เรียกตัวเองทุก 1 วินาที)"""
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        now = f"เวลาปัจจุบัน: {time_str}"
        self.clock_label.config(text=now)
        self.root.after(1000, self._update_time)  # เรียกใหม่ในอีก 1000ms
    
    # --- ฟังก์ชัน 'Handle' (ตัวกลางเชื่อมปุ่มกับ Simulator) ---

    def handle_route_in(self, platform):
        """ถูกเรียกเมื่อกดปุ่ม 'เส้นทางเข้า P1/P2'"""
        self.log_message(f"[CONTROL] Requesting INBOUND route to P{platform}...")
        self.sim.set_route_in(platform) # เรียกฟังก์ชันของ Sim

    def handle_route_out(self, platform):
        """ถูกเรียกเมื่อกดปุ่ม 'ออกเส้นทาง P1/P2'"""
        self.log_message(f"[CONTROL] Requesting OUTBOUND route from P{platform}...")
        self.sim.set_route_out(platform) # เรียกฟังก์ชันของ Sim
        
    def handle_arrive(self):
        """ถูกเรียกเมื่อกดปุ่ม 'รถไฟเข้า'"""
        self.log_message(f"[CONTROL] Simulating train arrival...")
        self.sim.call_train() # เรียกฟังก์ชันของ Sim
        
    def handle_emergency(self):
        """ถูกเรียกเมื่อกดปุ่ม 'หยุดฉุกเฉิน'"""
        self.log_message("[CONTROL] !! EMERGENCY STOP PRESSED !!")
        self.sim.emergency_stop() # เรียกฟังก์ชันของ Sim

    
    def _monitor(self):
        """
        ลูปหลักของ GUI (เรียกตัวเองทุก 100ms)
        ทำหน้าที่ตรวจสอบสถานะจาก Simulator แล้วอัปเดต UI
        """
        self._update_ui()
        self.root.after(100, self._monitor)  # เรียกใหม่ในอีก 100ms
        
    def _update_ui(self):
        """
        ฟังก์ชันสำคัญ: อัปเดตสถานะของ GUI (ปุ่ม, ไฟ, ข้อความ)
        ตามสถานะ (state) จาก Simulator
        """
        
        # 1. ดึงสถานะปัจจุบันจาก Simulator
        state = self.sim.state
        route = self.sim.route_locked
        p1_occ = self.sim.platform_occupied[1]
        p2_occ = self.sim.platform_occupied[2]
        train_id = self.sim.current_train_id
        
        # 2. คำนวณเงื่อนไขของ UI
        is_ready = state == "ready" and not route
        is_in_station = state == "in_station" and not route
        is_moving = state in ["running", "leaving"] or route
        
        # 3. อัปเดตสถานะปุ่ม (เปิด/ปิด)
        # ปุ่มตั้งทางเข้า: ต้อง 'พร้อม' และ ชานชาลา 'ว่าง'
        self.btn_route_p1.config(state="normal" if is_ready and not p1_occ else "disabled")
        self.btn_route_p2.config(state="normal" if is_ready and not p2_occ else "disabled")
        
        # ปุ่มรถไฟเข้า: ต้องมี 'เส้นทางเข้า (IN)' ตั้งไว้ และ สถานะ 'พร้อม'
        self.btn_arrive.config(state="normal" if route and route.endswith("_IN") and state == "ready" else "disabled")
        
        # ปุ่มตั้งทางออก: ต้อง 'จอดในสถานี' และ ชานชาลา 'มีรถ'
        self.btn_depart_p1.config(state="normal" if is_in_station and p1_occ else "disabled")
        self.btn_depart_p2.config(state="normal" if is_in_station and p2_occ else "disabled")

        # ปุ่มฉุกเฉิน: ปิดการใช้งานถ้ากำลังฉุกเฉินอยู่ (รอรีเซ็ต)
        self.btn_emergency.config(state="disabled" if state == "emergency" else "normal")

        # 4. อัปเดตไฟสัญญาณ
        # ตั้งค่าเริ่มต้นเป็นสีแดงทั้งหมด
        self.canvas.itemconfig(self.signal_1, fill="red")
        self.canvas.itemconfig(self.signal_p1_depart, fill="red")
        self.canvas.itemconfig(self.signal_p2_depart, fill="red")
        self.canvas.itemconfig(self.signal_3, fill="red")

        # เปลี่ยนเป็นสีเขียวตามเส้นทางที่ล็อก
        if route == "P1_IN":
            self.canvas.itemconfig(self.signal_1, fill="green") # S-01 เขียว
        elif route == "P2_IN":
            self.canvas.itemconfig(self.signal_1, fill="green") # S-01 เขียว
        elif route == "P1_OUT":
            self.canvas.itemconfig(self.signal_p1_depart, fill="green") # S-P1 เขียว
            self.canvas.itemconfig(self.signal_3, fill="green")      # S-03 เขียว
        elif route == "P2_OUT":
            self.canvas.itemconfig(self.signal_p2_depart, fill="green") # S-P2 เขียว
            self.canvas.itemconfig(self.signal_3, fill="green")      # S-03 เขียว
        
        # 5. อัปเดตข้อความสถานะ (Status Label)
        if state == "ready" and not route:
            self.status_label.config(text="สถานะ: พร้อม (Ready)", fg="green")
        elif state == "in_station":
            platform = self.sim.last_platform
            train_id_text = train_id if train_id else "รถไฟ"
            self.status_label.config(text=f"สถานะ: {train_id_text} จอดที่ P{platform}", fg="cyan")
        elif state == "running":
            train_id_text = train_id if train_id else "รถไฟ"
            self.status_label.config(text=f"สถานะ: {train_id_text} กำลังเข้า (Running)", fg="yellow")
        elif state == "leaving":
            train_id_text = train_id if train_id else "รถไฟ"
            self.status_label.config(text=f"สถานะ: {train_id_text} กำลังออก (Leaving)", fg="yellow")
        elif state == "emergency":
            self.status_label.config(text="สถานะ: หยุดฉุกเฉิน (EMERGENCY)", fg="red")
        elif route:
            self.status_label.config(text=f"สถานะ: ตั้งเส้นทางแล้ว ({route})", fg="orange")
        

# --- จุดเริ่มต้นของโปรแกรม ---
if __name__ == "__main__":
    root = tk.Tk()  # สร้างหน้าต่างหลัก
    app = TrainApp(root) # สร้างแอป GUI
    root.mainloop() # เริ่มการทำงานของ GUI