#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Base Retriever with FAISS
Индексирует JSONL файлы и извлекает релевантные фрагменты для RAG
"""

import json
import os
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Tuple


class KBRetriever:
    """RAG retriever для базы знаний X"""

    def __init__(self, kb_dir: str, mistral_client):
        """
        Инициализация retriever

        Args:
            kb_dir: путь к папке с JSONL файлами
            mistral_client: клиент Mistral AI для embeddings
        """
        self.kb_dir = Path(kb_dir)
        self.mistral_client = mistral_client
        self.documents = []  # список всех документов из KB
        self.embeddings = None  # numpy array с embeddings
        self.index = None  # FAISS индекс
        self.embedding_dim = 1024  # размерность mistral-embed

    def load_jsonl_files(self) -> List[Dict]:
        """Загрузить все JSONL файлы из kb директории"""
        documents = []

        # Получаем все .jsonl файлы
        jsonl_files = list(self.kb_dir.glob("*.jsonl"))

        for jsonl_file in jsonl_files:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:  # пропускаем пустые строки
                        try:
                            doc = json.loads(line)
                            # Добавляем источник файла
                            doc['source_file'] = jsonl_file.name
                            documents.append(doc)
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Ошибка парсинга JSON в {jsonl_file.name}: {e}")

        print(f"✅ Загружено {len(documents)} документов из {len(jsonl_files)} файлов")
        return documents

    def get_embedding(self, text: str) -> np.ndarray:
        """Получить embedding для текста через Mistral AI"""
        try:
            response = self.mistral_client.embeddings.create(
                model="mistral-embed",
                inputs=[text]
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            print(f"❌ Ошибка получения embedding: {e}")
            return np.zeros(self.embedding_dim, dtype=np.float32)

    def build_index(self):
        """Построить FAISS индекс из документов KB"""
        print("🔨 Строим индекс KB...")

        # Загружаем документы
        self.documents = self.load_jsonl_files()

        if not self.documents:
            print("⚠️ Нет документов для индексации!")
            return

        # Создаём embeddings для каждого документа
        embeddings_list = []

        for i, doc in enumerate(self.documents):
            # Комбинируем title и text для лучшего поиска
            text_to_embed = f"{doc.get('title', '')} {doc.get('text', '')}"

            embedding = self.get_embedding(text_to_embed)
            embeddings_list.append(embedding)

            if (i + 1) % 10 == 0:
                print(f"  Обработано {i + 1}/{len(self.documents)} документов")

        # Конвертируем в numpy array
        self.embeddings = np.array(embeddings_list, dtype=np.float32)

        # Создаём FAISS индекс (L2 distance)
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.index.add(self.embeddings)

        print(f"✅ Индекс построен: {self.index.ntotal} векторов")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Найти top_k наиболее релевантных документов

        Args:
            query: запрос пользователя (контекст диалога)
            top_k: количество документов для возврата

        Returns:
            Список документов с добавленным полем 'score'
        """
        if self.index is None:
            print("⚠️ Индекс не построен! Вызовите build_index() сначала")
            return []

        # Получаем embedding запроса
        query_embedding = self.get_embedding(query).reshape(1, -1)

        # Ищем ближайшие векторы
        distances, indices = self.index.search(query_embedding, top_k)

        # Формируем результат
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['score'] = float(distance)
                results.append(doc)

        return results

    def rebuild_index(self):
        """Пересобрать индекс (для обновления KB)"""
        print("🔄 Пересборка индекса...")
        self.build_index()

    def format_retrieved_context(self, retrieved_docs: List[Dict]) -> str:
        """
        Форматировать полученные документы в текстовый контекст

        Args:
            retrieved_docs: список документов из retrieve()

        Returns:
            Форматированный текст для промпта
        """
        if not retrieved_docs:
            return ""

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            title = doc.get('title', 'Без названия')
            text = doc.get('text', '')
            source = doc.get('source_file', 'unknown')

            context_parts.append(f"[{i}] {title}\n{text}\n(Источник: {source})")

        return "\n\n---\n\n".join(context_parts)

    def save_index(self, filepath: str):
        """Сохранить индекс в файл (опционально, для быстрой загрузки)"""
        if self.index is not None:
            faiss.write_index(self.index, filepath)
            print(f"💾 Индекс сохранён в {filepath}")

    def load_index(self, filepath: str):
        """Загрузить индекс из файла"""
        if os.path.exists(filepath):
            self.index = faiss.read_index(filepath)
            # Также нужно загрузить documents
            self.documents = self.load_jsonl_files()
            print(f"📂 Индекс загружен из {filepath}")
        else:
            print(f"⚠️ Файл {filepath} не найден")