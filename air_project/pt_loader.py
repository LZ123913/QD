"""
Pure-numpy loader for PyTorch state_dict .pt files (zip format, CPU float32).
No torch dependency.
"""
import zipfile
import pickle
import io
import struct
import numpy as np
from collections import OrderedDict


class _FloatStorage:
    def __init__(self, data):
        self.data = data  # numpy 1D array


class _TorchUnpickler(pickle.Unpickler):
    def __init__(self, file, zip_file):
        super().__init__(file)
        self.zip = zip_file
        self.storage_cache = {}

    def find_class(self, module, name):
        # Return stand-ins for torch classes
        if module == 'collections' and name == 'OrderedDict':
            return OrderedDict
        if module == 'torch._utils' and name == '_rebuild_tensor_v2':
            return _rebuild_tensor_v2
        if module == 'torch._utils' and name == '_rebuild_tensor':
            return _rebuild_tensor  # older format
        if module == 'torch' and name == 'FloatStorage':
            return 'FloatStorage'
        if module == 'torch' and name == 'LongStorage':
            return 'LongStorage'
        if module == 'torch' and name == 'DoubleStorage':
            return 'DoubleStorage'
        if module == 'torch' and name == 'IntStorage':
            return 'IntStorage'
        if module == 'torch' and name == 'HalfStorage':
            return 'HalfStorage'
        # For anything else (e.g. torch.Size), return a passthrough
        return _unknown_class(module, name)

    def persistent_load(self, pid):
        # pid is a tuple: (storage_type, storage_key, location, numel, ...)
        # Newer format: ('storage', storage_type, root_key, location, numel, view_metadata)
        if isinstance(pid, tuple) and len(pid) >= 4:
            storage_type = pid[1] if pid[0] == 'storage' else pid[0]
            key = pid[2] if pid[0] == 'storage' else pid[1]
            numel = pid[4] if pid[0] == 'storage' else pid[3]
        else:
            raise ValueError(f'Unexpected persistent id: {pid}')

        if key in self.storage_cache:
            return self.storage_cache[key]

        dtype_map = {
            'FloatStorage': (np.float32, 4),
            'DoubleStorage': (np.float64, 8),
            'HalfStorage': (np.float16, 2),
            'LongStorage': (np.int64, 8),
            'IntStorage': (np.int32, 4),
        }
        np_dtype, elem_size = dtype_map.get(storage_type, (np.float32, 4))

        data_path = f'archive/data/{key}'
        raw = self.zip.read(data_path)
        arr = np.frombuffer(raw, dtype=np_dtype, count=numel).copy()
        storage = _FloatStorage(arr)
        self.storage_cache[key] = storage
        return storage


def _unknown_class(module, name):
    def factory(*args, **kwargs):
        return (module, name, args, kwargs)
    return factory


def _rebuild_tensor_v2(storage, storage_offset, size, stride, requires_grad, backward_hooks):
    numel = 1
    for s in size:
        numel *= s
    t = storage.data[storage_offset: storage_offset + numel]
    return t.reshape(size)


def _rebuild_tensor(storage, storage_offset, size, stride):
    numel = 1
    for s in size:
        numel *= s
    t = storage.data[storage_offset: storage_offset + numel]
    return t.reshape(size)


def load_state_dict(path):
    """Load a .pt state_dict into an OrderedDict of numpy arrays."""
    with zipfile.ZipFile(path) as z:
        with z.open('archive/data.pkl') as f:
            unpickler = _TorchUnpickler(io.BytesIO(f.read()), z)
            state = unpickler.load()
    return state


if __name__ == '__main__':
    import os, sys
    folder = r'd:\vue_work\air-front\air_project'
    for fn in ['baseline_lstm.pt', 'baseline_gru.pt', 'cnn_lstm.pt', 'att_lstm.pt', 'ablation_noatt_lstm.pt']:
        p = os.path.join(folder, fn)
        if not os.path.exists(p):
            continue
        print(f'\n=== {fn} ===')
        try:
            sd = load_state_dict(p)
            for k, v in sd.items():
                if hasattr(v, 'shape'):
                    print(f'  {k}: {v.shape}  dtype={v.dtype}')
                else:
                    print(f'  {k}: {type(v)} = {v}')
        except Exception as e:
            import traceback
            traceback.print_exc()
