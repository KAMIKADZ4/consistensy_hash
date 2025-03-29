import hashlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
import random
import colorsys
from collections import deque


def get_contrast_colors(n, seed=100, pastel_factor=0.7):
    if seed is not None:
        random.seed(seed)
    
    # Используем золотое сечение для равномерного распределения оттенков
    golden_ratio = 0.618033988749895
    colors = []
    
    for i in range(n):
        # Равномерное распределение оттенков с использованием золотого сечения
        hue = (i * golden_ratio) % 1.0
        
        # Яркость и насыщенность для контраста
        saturation = 0.7 + random.uniform(0, 0.3) * pastel_factor
        value = 0.8 + random.uniform(0, 0.2) * pastel_factor
        
        # Конвертируем HSV в RGB
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(rgb)
    
    return colors

_color_wheel = deque()
def get_contrast_color(seed=None):
    """
    Генерирует последовательность контрастных цветов при каждом вызове
    (запоминает предыдущие цвета для избежания повторов)
    """
    global _color_wheel
    
    if seed is not None:
        random.seed(seed)
        _color_wheel = deque()
    
    if not _color_wheel:
        # Заполняем колесо новыми цветами при необходимости
        new_colors = get_contrast_colors(12, pastel_factor=0.8)
        _color_wheel.extend(new_colors)
    
    return _color_wheel.popleft()

class ConsistentHashingVisualizer:
    def __init__(self, max_value=65535, replicas=3):
        self.max_value = max_value
        self.servers = {}
        self.server_colors = {}
        self.objects = []
        self.replicas = replicas
    
    def hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.max_value

    def add_server(self, server_name):
        """Добавляет сервер с виртуальными узлами на числовую прямую"""
        color = get_contrast_color()  # Генерация случайного цвета для сервера
        self.server_colors[server_name] = color
        
        for i in range(self.replicas):
            # Хешируем "сервер:i" для создания виртуального узла
            key = f"{server_name}_{i}"
            hash_val = self.hash(key)
            
            self.servers[hash_val] = (server_name, color)
            type_ = 'server_main' if i == 0 else 'server_virtual'
            self.objects.append((hash_val, server_name, type_))
    
    def remove_server(self, server_name):
        del self.server_colors[server_name]

        server_hashes = sorted(self.servers.keys(), reverse=True)
        assigned_server = None
        
        for h in server_hashes:
            if self.servers[h][0].startswith(server_name):
                    self.servers[h] = assigned_server
            else:
                assigned_server = self.servers[h]

        # TODO перекрасить объекты


    def add_object(self, object_name):
        """Добавляет объект на числовую прямую"""
        hash_val = self.hash(object_name)
        
        # Находим ближайший сервер справа
        server_hashes = sorted(self.servers.keys())
        assigned_server = None
        
        for h in server_hashes:
            if h >= hash_val:
                assigned_server = self.servers[h][0]
                break
        
        # Если хеш объекта больше всех серверов, берем первый сервер
        if assigned_server is None and server_hashes:
            assigned_server = self.servers[server_hashes[0]][0]
        
        if assigned_server:
            self.objects.append((hash_val, assigned_server, 'object'))
            return assigned_server
        return None

    def stats(self):
        servers = sorted(
            list(self.servers.items()),
            key=lambda x: x[0]
        )
        last_val = 0
        res = {}
        for hash_val, info in servers:
            res[info] = res.get(info, 0) + (hash_val - last_val)
            last_val = hash_val
        res[servers[0][1]] += self.max_value - last_val
        for i in res:
            print(i[0], 'покрывает', res[i], 'значений')
        print('Кол-во нод:', len(self.servers))
        return res
    
    def visualize_with_piechart(self):
        """Визуализирует числовую прямую с серверами и объектами"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                gridspec_kw={'height_ratios': [2, 1]})
        
        # Рисуем числовую прямую
        ax1.plot([0, self.max_value], [0, 0], 'k-', alpha=0.3)
        
        # Рисуем серверы и объекты
        server_handles = {}
        for point, server, point_type in self.objects:
            color = self.server_colors.get(server, 'gray')
            if point_type == 'server_virtual':
                marker = '^'
                size = 70
            elif point_type == 'server_main':
                marker = 's'
                size = 120
            else:
                marker = 'o'
                size = 30
            
            plot = ax1.scatter(point, 0, c=[color], marker=marker, s=size, edgecolors='black')
            if server not in server_handles:
                server_handles[server] = plot
        
        # Настройка графика
        ax1.set_yticks([])
        ax1.set_xlim(0, self.max_value)
        ax1.set_title(f"Консистентное хеширование (диапазон 0-{self.max_value}, серверов={len(self.server_colors)}, виртуальных={self.replicas})")
        ax1.set_xlabel("Хеш-значения")
        
        # Легенда
        legend_elements = [Patch(facecolor=color, edgecolor='black', label=server) 
                          for server, color in self.server_colors.items()]
        ax1.legend(handles=legend_elements, loc='upper right')
        
        ax1.grid(True, linestyle='--', alpha=0.5)

        server_data = self.stats()
        labels = [name for (name, _) in server_data.keys()]
        sizes = list(server_data.values())
        colors = [color for (_, color) in server_data.keys()]
        
        # Рисуем диаграмму
        wedges, texts, autotexts = ax2.pie(
            sizes, 
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': 'black', 'linewidth': 1}
        )
        
        # Настраиваем отображение процентов
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
        
        ax2.set_title("Распределение данных по серверам")
        ax2.axis('equal')  # Круглая, а не эллиптическая диаграмма


        plt.tight_layout()
        plt.show()


# Пример использования
if __name__ == "__main__":
    ch = ConsistentHashingVisualizer(2**32, replicas=100)
    
    # Добавляем серверы
    ch.add_server("server1")
    ch.add_server("server2")
    ch.add_server("server3")
    ch.add_server("server4")
    ch.add_server("server5")
    
    # Добавляем случайные объекты
    # for i in range(500):
    #     ch.add_object(f"object_{i}")
    
    # Визуализация
    ch.visualize_with_piechart()

    ch.remove_server("server5")
    ch.visualize_with_piechart()
    
