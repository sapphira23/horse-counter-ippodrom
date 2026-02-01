from ultralytics import YOLO
import cv2


class Model:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')


    def get_processed_images(self, source_path, target_dir, draw_bbox=True, conf_level = 0.4):
        results = self.model.predict(
                source=source_path,
                classes=[17],
                conf=conf_level,
                save=draw_bbox,
                project=target_dir,
                name='output',
                exist_ok=True
            )
        
        self.draw_boxes(source_path, results, source_path)

        return len(results[0].boxes)


    def draw_boxes(self, image_path, results, output_path):
        img = cv2.imread(image_path)
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            label = f"Horse: {conf:.2f}"
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.putText(img, label, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imwrite(output_path, img)

