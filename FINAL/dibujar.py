import cv2
from picamera2 import Picamera2
import numpy as np

# Rangos de colores en HSV
LOWER_COLOR_BLUE = np.array([90, 50, 50])
UPPER_COLOR_BLUE = np.array([130, 255, 255])

LOWER_COLOR_YELLOW = np.array([20, 100, 100])
UPPER_COLOR_YELLOW = np.array([30, 255, 255])

LOWER_COLOR_GREEN = np.array([40, 100, 100])
UPPER_COLOR_GREEN = np.array([80, 255, 255])

LOWER_COLOR_RED1 = np.array([0, 100, 100])
UPPER_COLOR_RED1 = np.array([10, 255, 255])

LOWER_COLOR_RED2 = np.array([170, 100, 100])
UPPER_COLOR_RED2 = np.array([180, 255, 255])

LOWER_COLOR_BLACK = np.array([0, 0, 0])
UPPER_COLOR_BLACK = np.array([180, 255, 30])

LOWER_COLOR_ORANGE = np.array([5, 100, 100])
UPPER_COLOR_ORANGE = np.array([15, 255, 255])

# TRACKER
def tracker(frame, prev_x, prev_y, trajectory, is_tracking):
    # Convertir el frame de BGR a HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # color en HSV (azul)
    lower_color = LOWER_COLOR_YELLOW
    upper_color = UPPER_COLOR_YELLOW

    # Crear una máscara para el color que nos pasan y aplicarla al frame
    mask = cv2.inRange(hsv, lower_color, upper_color)

    # Encontrar contornos en la máscara
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Si se detecta algún contorno
    if contours:
        # Encontrar el contorno más grande (círculo)
        largest_contour = max(contours, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)
        # Asegurarse de que el radio sea lo suficientemente grande para ser considerado como el círculo
        if radius > 10:
            # Convertir las coordenadas a números enteros
            x, y, radius = int(x), int(y), int(radius)
            # Dibujar el círculo y su centro
            cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            # Dibujar la trayectoria
            if prev_x is not None and prev_y is not None:
                cv2.line(frame, (prev_x, prev_y), (x, y), (0, 0, 255), 5)
                # Almacenar las coordenadas para la trayectoria
                if is_tracking == True:
                    trajectory.append((x, y))
            # Actualizar las coordenadas previas
            prev_x, prev_y = x, y
    return frame, prev_x, prev_y, trajectory


# Dibujar la trayectoria del objeto en el frame
def draw_trajectory(frame, trajectory):
    # Dibujar la trayectoria almacenada
    for i in range(1, len(trajectory)):
        cv2.line(frame, trajectory[i - 1], trajectory[i], (255, 255, 0), 15)
    return frame


# Funcion para dibujar 1 cuadrado sobre el video
def overlay_square(frame):
    # Dibujar un cuadrado en el centro y muy grande
    centro = (frame.shape[1] // 2, frame.shape[0] // 2)
    cv2.rectangle(frame, (centro[0] - 100, centro[1] - 100), (centro[0] + 100, centro[1] + 100), (255, 0, 0), 20)
    return frame


# Funcion para dibujar 1 triangulo sobre el video
def overlay_triangle(frame):
    # Dibujar un triangulo
    pts = np.array([[100, 300], [200, 200], [300, 300]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(frame, [pts], True, (0, 255, 255), 5)
    return frame


# Función para comparar la trayectoria con el cuadrado
def compare_trajectory_square(trajectory):
    # Crear un cuadrado perfecto en una imagen en blanco
    img1 = np.zeros((640, 480, 3), np.uint8)
    centro = (img1.shape[1] // 2, img1.shape[0] // 2)
    cv2.rectangle(img1, (centro[0] - 100, centro[1] - 100), (centro[0] + 100, centro[1] + 100), (255, 0, 0), 20)

    # Crear una imagen en blanco y dibujar la trayectoria
    img2 = np.zeros((640, 480, 3), np.uint8)
    for i in range(1, len(trajectory)):
        cv2.line(img2, trajectory[i - 1], trajectory[i], (255, 0, 0), 20)

    # Convertir imágenes a escala de grises
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Encontrar contornos en ambas imágenes
    contours1, _ = cv2.findContours(gray1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours2, _ = cv2.findContours(gray2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Obtener el contorno del cuadrado perfecto
    contour1 = max(contours1, key=cv2.contourArea)
    
    # Calcular la distancia entre los contornos del cuadrado y la trayectoria
    distances = [cv2.matchShapes(contour1, contour2, cv2.CONTOURS_MATCH_I2, 0.0) for contour2 in contours2]

    if len(distances) == 0:
        return False
    
    # Si la distancia más pequeña es menor a un umbral, consideramos que el cuadrado está bien
    min_distance = min(distances)
    print(min_distance, max(distances))
    if min_distance < 0.1:  # Ajusta el umbral según sea necesario
        return True
    else:
        return False


    

if __name__ == "__main__":

    picam = Picamera2()
    picam.video_configuration.main.size = (640, 480)
    picam.preview_configuration.main.format = "RGB888"
    picam.preview_configuration.align()
    picam.configure("preview")
    picam.start()
    prev_x, prev_y = None, None
    trajectory = []
    is_tracking = False
    while True:
        frame = picam.capture_array()
        
        # Realizar el seguimiento de de los objetos
        frame, prev_x, prev_y, trajectory = tracker(frame, prev_x, prev_y, trajectory, is_tracking)

        # Dibujar la trayectoria en el frame
        frame_with_trajectory = draw_trajectory(frame.copy(), trajectory)

        # Dibujar un cuadrado
        frame_with_square = overlay_square(frame_with_trajectory)

        # comparamos la trayectoria con el cuadrado
        if compare_trajectory_square(trajectory):
            texto_video = "El cuadrado esta bien"
        else:
            texto_video = "El cuadrado esta mal"

        frame_flipped = frame_with_square[:, ::-1, :]
        # cv2.putText(frame_flipped, texto_video, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow("picam", frame_flipped)

        # Detectar tecla pulsada
        key = cv2.waitKey(1)
        if key == ord('s'):
            is_tracking = True
        elif key == ord('e'):
            is_tracking = False
            trajectory = []
            prev_x = None
            prev_y = None
        elif key == ord('q'):
            break
    cv2.destroyAllWindows()