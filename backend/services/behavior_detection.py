"""
Servicio de Detección de Comportamiento
Encapsula la lógica de detección de comportamientos (PELEA, DISTURBIO, etc) usando LSTM.
"""

import os
import json
import numpy as np
import torch
import torch.nn as nn
from collections import deque

class ActionLSTM(nn.Module):
    """Modelo LSTM para clasificación de acciones."""
    def __init__(self, input_size=68, hidden_size=128, num_classes=3):
        super(ActionLSTM, self).__init__()
        self.fc_in = nn.Linear(input_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size, batch_first=True, bidirectional=True)
        self.fc_out = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, x):
        x = self.fc_in(x)
        out, _ = self.lstm(x)
        out = self.fc_out(out[:, -1, :])
        return out


class BehaviorDetectionService:
    def __init__(self, model_path=None, label_map_path=None):
        """
        Inicializa el servicio de detección de comportamiento.
        
        Args:
            model_path: Ruta al modelo LSTM entrenado
            label_map_path: Ruta al archivo JSON con el mapeo de etiquetas
        """
        self.device = torch.device('cpu')
        
        if model_path is None:
            model_path = os.getenv('LSTM_MODEL_PATH', 'models/lstm_3clasesstride1.pt')
        
        if label_map_path is None:
            label_map_path = os.getenv('LABEL_MAP_PATH', 'models/label_map_3clases.json')
        
        # Cargar modelo
        self.model = ActionLSTM(68, 128, 3).to(self.device)
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
        except Exception as e:
            raise RuntimeError(f"Error cargando modelo LSTM: {e}")
        
        # Cargar mapeo de etiquetas
        try:
            with open(label_map_path, 'r', encoding='utf-8') as f:
                lm = json.load(f)
                self.id2label = {int(v): k for k, v in lm['label2id'].items()}
        except Exception as e:
            raise RuntimeError(f"Error cargando label_map: {e}")
        
        self.window_size = 32  # Tamaño de ventana para secuencias
    
    def preprocess_keypoints_sequence(self, keypoints_sequence):
        """
        Preprocesa una secuencia de keypoints para el modelo LSTM.
        
        Args:
            keypoints_sequence: Array de shape (T, 17, 2) con keypoints de T frames
            
        Returns:
            Array procesado de shape (T, 68)
        """
        seq = keypoints_sequence.copy().astype(np.float32)
        
        # Normalizar respecto al primer frame
        ref = seq[:, 0:1, :]
        seq = seq - ref
        
        # Normalizar por distancia máxima
        max_dist = np.linalg.norm(seq.reshape(seq.shape[0], -1), axis=1).max()
        if max_dist > 0:
            seq = seq / max_dist
        
        # Calcular deltas (velocidades)
        deltas = np.zeros_like(seq)
        deltas[1:] = seq[1:] - seq[:-1]
        
        # Concatenar posiciones y velocidades
        feat = np.concatenate([seq, deltas], axis=-1)
        T, K, C = feat.shape
        
        return feat.reshape(T, K * C).astype(np.float32)
    
    def predict_behavior(self, keypoints_sequence, confidence_threshold=0.5):
        """
        Predice el comportamiento a partir de una secuencia de keypoints.
        
        Args:
            keypoints_sequence: Array de shape (T, 17, 2)
            confidence_threshold: Umbral de confianza mínima
            
        Returns:
            dict con predicción, etiqueta y confianza
        """
        try:
            # Preprocesar
            x = self.preprocess_keypoints_sequence(keypoints_sequence)
            
            # Convertir a tensor
            xb = torch.tensor(x, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # Predecir
            with torch.no_grad():
                logits = self.model(xb)
                probs = torch.nn.functional.softmax(logits, dim=1)
                prob_values = probs.cpu().numpy()[0]
            
            best_idx = int(np.argmax(prob_values))
            best_label = self.id2label.get(best_idx, 'UNKNOWN')
            best_prob = float(prob_values[best_idx])
            
            return {
                'behavior': best_label,
                'confidence': best_prob,
                'all_probs': {self.id2label.get(i, 'UNKNOWN'): float(p) 
                            for i, p in enumerate(prob_values)},
                'is_valid': best_prob >= confidence_threshold
            }
        except Exception as e:
            return {
                'behavior': 'ERROR',
                'confidence': 0.0,
                'error': str(e),
                'is_valid': False
            }
