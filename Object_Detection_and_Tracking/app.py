import cv2
import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from ultralytics import YOLO
from scipy.optimize import linear_sum_assignment
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------- Simple SORT-style tracker ----------------
class CentroidTracker:
    """Lightweight centroid tracker for assigning persistent object IDs."""
    def __init__(self, max_distance=80, max_missing=12):
        self.next_id = 1
        self.objects = {}
        self.missing = {}
        self.max_distance = max_distance
        self.max_missing = max_missing

    def update(self, detections):
        # detections = [(x1,y1,x2,y2), ...]
        centers = []
        for box in detections:
            x1, y1, x2, y2 = box
            centers.append(((x1 + x2) / 2, (y1 + y2) / 2))

        if not self.objects:
            for center in centers:
                self.objects[self.next_id] = center
                self.missing[self.next_id] = 0
                self.next_id += 1
            return list(zip(self.objects.keys(), centers))

        ids = list(self.objects.keys())
        old = np.array([self.objects[i] for i in ids], dtype=np.float32)
        new = np.array(centers, dtype=np.float32)

        if len(new) == 0:
            for obj_id in ids:
                self.missing[obj_id] += 1
            self._remove_lost()
            return []

        distance = np.linalg.norm(old[:, None, :] - new[None, :, :], axis=2)
        rows, cols = linear_sum_assignment(distance)

        used_old, used_new = set(), set()
        results = []

        for r, c in zip(rows, cols):
            if distance[r, c] <= self.max_distance:
                obj_id = ids[r]
                self.objects[obj_id] = tuple(new[c])
                self.missing[obj_id] = 0
                used_old.add(r)
                used_new.add(c)
                results.append((obj_id, tuple(new[c])))

        for r, obj_id in enumerate(ids):
            if r not in used_old:
                self.missing[obj_id] += 1

        for c, center in enumerate(centers):
            if c not in used_new:
                self.objects[self.next_id] = center
                self.missing[self.next_id] = 0
                results.append((self.next_id, center))
                self.next_id += 1

        self._remove_lost()
        return results

    def _remove_lost(self):
        for obj_id in list(self.missing):
            if self.missing[obj_id] > self.max_missing:
                self.objects.pop(obj_id, None)
                self.missing.pop(obj_id, None)

    def reset(self):
        self.next_id = 1
        self.objects.clear()
        self.missing.clear()


class DetectorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VisionTrack • Object Detection & Tracking")
        self.geometry("1150x760")
        self.minsize(950, 650)

        self.cap = None
        self.running = False
        self.model = None
        self.tracker = CentroidTracker()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="👁 VisionTrack",
                     font=ctk.CTkFont(size=32, weight="bold")).grid(
                     row=0, column=0, pady=(20, 2))
        ctk.CTkLabel(self,
                     text="YOLO object detection + persistent object tracking",
                     text_color="#9aa4b2").grid(row=1, column=0, pady=(0, 12))

        main = ctk.CTkFrame(self, corner_radius=18)
        main.grid(row=2, column=0, padx=22, pady=8, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(
            main, text="Choose a video or start the webcam\n\n🎥 Live detection will appear here",
            corner_radius=14, fg_color="#111827",
            font=ctk.CTkFont(size=18)
        )
        self.video_label.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=3, column=0, pady=8)

        ctk.CTkButton(controls, text="📷 Webcam", width=125,
                      command=self.start_webcam).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="🎞 Open Video", width=135,
                      command=self.open_video).pack(side="left", padx=5)
        self.stop_btn = ctk.CTkButton(controls, text="⏹ Stop", width=100,
                                      fg_color="#b91c1c", hover_color="#991b1b",
                                      command=self.stop).pack(side="left", padx=5)

        self.status = ctk.CTkLabel(self,
                                   text="Ready • First run downloads YOLOv8n model",
                                   text_color="#7dd3fc")
        self.status.grid(row=4, column=0, pady=(0, 12))

        self.protocol("WM_DELETE_WINDOW", self.close)

    def load_model(self):
        if self.model is None:
            self.status.configure(text="⏳ Loading YOLO model...", text_color="#fbbf24")
            self.update_idletasks()
            self.model = YOLO("yolov8n.pt")
        self.status.configure(text="✓ Model loaded", text_color="#86efac")

    def start_webcam(self):
        self.stop()
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open the webcam.")
            return
        self.run_detection()

    def open_video(self):
        path = filedialog.askopenfilename(
            title="Select a video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if not path:
            return
        self.stop()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            messagebox.showerror("Video Error", "Could not open the selected video.")
            return
        self.run_detection()

    def run_detection(self):
        try:
            self.load_model()
        except Exception as exc:
            messagebox.showerror(
                "Model Error",
                f"Could not load YOLO.\n\n{exc}\n\nRun: pip install -r requirements.txt"
            )
            self.stop()
            return

        self.tracker.reset()
        self.running = True
        self.process_frame()

    def process_frame(self):
        if not self.running or self.cap is None:
            return

        ok, frame = self.cap.read()
        if not ok:
            self.stop()
            self.status.configure(text="Video finished", text_color="#7dd3fc")
            return

        frame = cv2.resize(frame, (900, 560))
        result = self.model(frame, verbose=False)[0]

        boxes = []
        labels = []
        scores = []

        if result.boxes is not None:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf < 0.45:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cls = int(box.cls[0])
                boxes.append((x1, y1, x2, y2))
                labels.append(self.model.names[cls])
                scores.append(conf)

        tracks = self.tracker.update(boxes)

        # Match a track center to the closest current detection box.
        for track_id, center in tracks:
            cx, cy = center
            best = -1
            best_dist = float("inf")
            for i, box in enumerate(boxes):
                bx = (box[0] + box[2]) / 2
                by = (box[1] + box[3]) / 2
                d = ((cx - bx) ** 2 + (cy - by) ** 2) ** 0.5
                if d < best_dist:
                    best_dist = d
                    best = i

            if best >= 0 and best_dist < 120:
                x1, y1, x2, y2 = boxes[best]
                label = labels[best]
                conf = scores[best]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 60), 2)
                text = f"{label}  ID:{track_id}  {conf:.0%}"
                cv2.rectangle(frame, (x1, max(0, y1-28)), (x1+len(text)*9, y1), (255, 200, 60), -1)
                cv2.putText(frame, text, (x1+5, y1-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 2)

        active = len(tracks)
        cv2.putText(frame, f"Objects tracked: {active}",
                    (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((900, 560))
        photo = ImageTk.PhotoImage(image=image)
        self.video_label.configure(image=photo, text="")
        self.video_label.image = photo

        self.status.configure(
            text=f"● LIVE   Objects tracked: {active}",
            text_color="#86efac"
        )
        self.after(15, self.process_frame)

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def close(self):
        self.stop()
        self.destroy()

if __name__ == "__main__":
    DetectorApp().mainloop()
