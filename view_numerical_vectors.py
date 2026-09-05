# ==============================================================================
# File: view_numerical_vectors.py
# Purpose: Visual inspector showing the raw 768-dimensional numerical vectors (embeddings).
# ==============================================================================

from app.services.embedding_service import get_text_embedding

sample_chunk_text = 'Operating systems manage computer hardware and provide memory isolation.'

# 1. Generate the 768-dimensional numerical vector
vector = get_text_embedding(sample_chunk_text, task_type='RETRIEVAL_DOCUMENT')

print('=' * 75)
print('ORIGINAL TEXT CHUNK:')
print(' ', sample_chunk_text)
print('=' * 75)
print(f'TOTAL NUMERICAL DIMENSIONS: {len(vector)} numbers')
print('=' * 75)
print('\nFIRST 20 NUMBERS (Coordinates in concept space):')
for i, val in enumerate(vector[:20]):
    print(f'  Dimension [{i+1:03d}]: {val:+.6f}')

print('  ...')
print(f'  Dimension [768]: {vector[-1]:+.6f}')
print('=' * 75)
print('\nWHAT COMPUTERS SEE (Vector Array Preview):')
print('[', ', '.join(f'{x:.4f}' for x in vector[:10]), '... ]')
print('=' * 75)
