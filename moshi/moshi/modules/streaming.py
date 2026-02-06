# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# Copyright (c) Kyutai, all rights reserved.
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""
Streaming module API that should be implemented by all Streaming components,
"""

import abc
from contextlib import contextmanager
from dataclasses import dataclass, fields, is_dataclass
import itertools
import math
import json
from typing import List, Union, Protocol, TypeVar, Generic, Any, Optional
import torch
from safetensors.torch import save_file, load_file


class Resetable(Protocol):
    def reset(self) -> None:
        pass


State = TypeVar("State", bound=Resetable)
StreamingStateDict = dict[str, Union[torch.Tensor, int, float, str, bool, None]]


def is_dataclass_instance(obj):
    """Check if obj is an instance of a dataclass (not the class itself).
    
    Parameters
    ----------
    obj : Any
        Object to check.
        
    Returns
    -------
    bool
        True if obj is an instance of a dataclass, False otherwise.
    """
    return is_dataclass(obj) and not isinstance(obj, type)


def _restore_streaming_state_pt(value: torch.Tensor,
                                name: str,
                                state_dict: dict[str, torch.Tensor],
                                ):
    """Restore the streaming state from the given pt_state dict
    
    Parameters
    ----------
    value : torch.Tensor
        Specific streaming state tensor that needs to be set.
    name : str
        Name of the tensor in the state dict.
    state_dict: StreamingStateDict
        Flattened state dict containing the values to set.
    """
    if name in state_dict:
        value.copy_(state_dict[name].to(value.device))
        state_dict.pop(name)
    else:
        raise KeyError(f"Expected to find a streaming state for {name}.")

    
def _set_streaming_state_inplace(streaming_state: State,
                                 state_dict: StreamingStateDict,
                                 prefix: str,
                                 device: torch.device,
                                 ):
    """Set the streaming state in-place from the given `state_dict` dict.

    Parameters
    ----------
    streaming_state : State
        Specific streaming state object that needs to be set.
    state_dict: StreamingStateDict
        Flattened state dict containing the values to set.
    prefix : str
        Prefix to add to each key when looking up in `state_dict`.
    device : torch.device
        Device to move tensors to if needed.
    """
    if isinstance(streaming_state, torch.Tensor):
        _restore_streaming_state_pt(streaming_state, prefix, state_dict)
    elif is_dataclass_instance(streaming_state):
        _restore_streaming_state_from_keys(streaming_state, state_dict, prefix, [field.name for field in fields(streaming_state)], device)
    elif hasattr(streaming_state, "asdict"):
        _restore_streaming_state_from_keys(streaming_state, state_dict, prefix, list(streaming_state.asdict().keys()), device)
    else:
        raise TypeError(f"Unsupported type {type(streaming_state)} for streaming state with prefix {prefix}.")


def _restore_streaming_state_from_keys(streaming_state: State,
                                       state_dict: StreamingStateDict,
                                       prefix: str,
                                       keys: List[str],
                                       device: torch.device,
                                       ):
    """Restores the streaming state from the given `state_dict` dict
    looking up fields by adding `prefix` to each key in `keys` to look
    up values.
    `torch.Tensor` are copied to `device` if no `torch.Tensor` is already present
    otherwise, the data is copied to the device of the existing `torch.Tensor`.
    
    Parameters
    ----------
    streaming_state : State
        Specific streaming state object that needs to be set.
    state_dict: StreamingStateDict
        Flattened state dict containing the values to set.
    prefix : str
        Prefix to add to each key when looking up in `state_dict`.
    keys : List[str]
        List of keys to look up in `state_dict`.
    device : torch.device
        Device to move tensors to if needed.
    """
    for key in keys:
        full_key = f"{prefix}.{key}"
        existing_value = getattr(streaming_state, key)
        if isinstance(existing_value, torch.Tensor):
            _restore_streaming_state_pt(existing_value, full_key, state_dict)
        elif isinstance(existing_value, (int, float, str, bool, type(None))):
            if full_key in state_dict:
                restored_value = state_dict[full_key]
                if isinstance(restored_value, torch.Tensor):
                    restored_value = restored_value.to(device)
                setattr(streaming_state, key, restored_value)
                
                state_dict.pop(full_key)
            else:
                raise RuntimeError(f"Key {full_key} not found in state_dict.")
        else:
            _set_streaming_state_inplace(existing_value, state_dict, full_key, device)


def safe_asdict(dataclass_obj):
    """
    safe_asdict(dataclass_obj)

    Converts a dataclass object to a dict, skipping empty nested
    dataclasses without requiring values to be pickleable.
    
    Parameters
    ----------
    dataclass_obj : Any
        Dataclass object to convert.
        
    Returns
    -------
    dict
        Dictionary representation of the dataclass object.
    """
    out = {}
    for field in fields(dataclass_obj):
        value = getattr(dataclass_obj, field.name)
        if is_dataclass_instance(value):
            subvalue = safe_asdict(value)
            if len(subvalue) > 0:
                out[field.name] = subvalue
        else:
            out[field.name] = value
    return out
        

def _flatten_streaming_state(state_dict: dict[str, torch.Tensor],
                             state_dict_metadata: dict[str, Union[int, float, str, None]],
                             state: dict[str, State],
                             prefix: str,
                             ):
    """
    _flatten_streaming_state(state_dict, state_dict_metadata, state, prefix)

    Helper function for recursively flattening the streaming state into a dict of tensors
    and a dict of metadata (non-tensor values).

    Parameters
    ----------
    state_dict : dict[str, torch.Tensor]
        Dictionary to store the flattened tensor states.
    state_dict_metadata : dict[str, Union[int, float, str, None]]
        Dictionary to store the flattened non-tensor states.
    state : dict[str, State]
        The streaming state to flatten.
    prefix : str
        Prefix to add to each key in the flattened state.
    """
    for key, value in state.items():
        if isinstance(value, torch.Tensor):
            state_dict[f"{prefix}{key}"] = value.contiguous()
        elif is_dataclass_instance(value):
            _flatten_streaming_state(state_dict, state_dict_metadata, safe_asdict(value), prefix=f"{prefix}{key}.")
        elif isinstance(value, dict):
            _flatten_streaming_state(state_dict, state_dict_metadata, value, prefix=f"{prefix}{key}.")
        elif isinstance(value, (str, int, float, bool, type(None))):
            state_dict_metadata[f"{prefix}{key}"] = value
        elif hasattr(value, "asdict"):
            _flatten_streaming_state(state_dict, state_dict_metadata, value.asdict(), prefix=f"{prefix}{key}.")
        else:
            raise TypeError(f"Unsupported type {type(value)} for key {key} (prefix={prefix}) in streaming state.")


def load_streaming_state(path: str,
                         metadata_path: str,
                         device: Union[str, int] = 'cpu',
                         ) -> StreamingStateDict:
    """
    load_streaming_state(path, metadata_path)

    Loads a streaming state from a safetensors file and its associated metadata json file.

    Parameters
    ----------
    str : path
        Path to the safetensors file.
    str : metadata_path
        Path to the metadata json file.
    device : Union[str, int], optional
        Device to load the tensors onto, by default 'cpu'.

    Returns
    -------
    dict
        The loaded streaming state flattened as a dictionary.
    """
    state_dict = load_file(path, device=device)
    with open(metadata_path, "rt", encoding="utf-8") as fin:
        state_dict_metadata = json.load(fin)
    state_dict.update(state_dict_metadata)
    return state_dict


class StreamingModule(abc.ABC, torch.nn.Module, Generic[State]):
    """Common API for streaming components.

    Each streaming component has a streaming state, which is just a dict[str, Tensor].
    By convention, the first dim of each tensor must be the batch size.
    Don't use dots in the key names, as this would clash with submodules
    (like in state_dict).

    If `self._is_streaming` is True, the component should use and remember
    the proper state inside `self._streaming_state`.

    To set a streaming component in streaming state, use

        with module.streaming():
            ...

    This will automatically reset the streaming state when exiting the context manager.
    This also automatically propagates to all streaming children module.

    Some module might also implement the `StreamingModule.flush` method, although
    this one is trickier, as all parents module must be StreamingModule and implement
    it as well for it to work properly. See `StreamingSequential` after.
    """

    def __init__(self) -> None:
        super().__init__()
        self._streaming_state: State | None = None
        self._streaming_propagate: bool = True

    @property
    def is_streaming(self):
        return self._streaming_state is not None

    def set_streaming_propagate(self, streaming_propagate: bool):
        self._streaming_propagate = streaming_propagate

    def _apply_named_streaming(self, fn: Any):
        def _handle_module(prefix: str, module: torch.nn.Module, recurse: bool = True):
            propagate = True
            if isinstance(module, StreamingModule):
                if module._streaming_propagate:
                    fn(prefix, module)
                else:
                    propagate = False
            if not recurse:
                return
            if propagate:
                for name, child in module.named_children():
                    _handle_module(prefix + "." + name, child)

        _handle_module("", self, recurse=False)
        for name, child in self.named_children():
            _handle_module(name, child)

    def _start_streaming(self, batch_size: int):
        def _start_streaming(name: str, module: StreamingModule):
            module._streaming_state = module._init_streaming_state(batch_size)

        self._apply_named_streaming(_start_streaming)

    def _stop_streaming(self):
        def _stop_streaming(name: str, module: StreamingModule):
            module._streaming_state = None

        self._apply_named_streaming(_stop_streaming)

    @abc.abstractmethod
    def _init_streaming_state(self, batch_size: int) -> State: ...

    def streaming_forever(self, batch_size: int):
        self._start_streaming(batch_size)

    @contextmanager
    def streaming(self, batch_size: int):
        """Context manager to enter streaming mode. Reset streaming state on exit."""

        self._start_streaming(batch_size)
        try:
            yield
        finally:
            self._stop_streaming()

    def reset_streaming(self):
        """Reset the streaming state."""

        def _reset(name: str, module: StreamingModule):
            state = module._streaming_state
            if state is None:
                raise ValueError(
                    f"Trying to reset streaming, but {name} wasn't streaming."
                )
            state.reset()

        self._apply_named_streaming(_reset)

    def get_streaming_state(self) -> dict[str, Any]:
        """Return the complete streaming state, including that of sub-modules."""
        state: dict[str, Any] = {}

        def _add(name: str, module: StreamingModule):
            state[name] = module._streaming_state

        self._apply_named_streaming(_add)
        return state

    def save_streaming_state(self,
                             save_path: str,
                             metadata_save_path: str,
                             extra_state_dict: Optional[dict[str, torch.Tensor]] = None,
                             ):
        """Save the streaming state, including that of sub-modules, to the given paths.
        
        Parameters
        ----------
        save_path : str
            Path to save the streaming state tensors (safetensors format).
        metadata_save_path : str
            Path to save the streaming state metadata (json format).
        extra_state_dict : Optional[dict[str, torch.Tensor]], optional
            Extra state dict to include in the saved streaming state tensors, by default None.
        """
        state_dict = {}
        if extra_state_dict is not None:
            state_dict.update(extra_state_dict)
        state_dict_metadata = {}
        state = self.get_streaming_state()
        _flatten_streaming_state(state_dict, state_dict_metadata, state, prefix="")
        save_file(state_dict, save_path)
        with open(metadata_save_path, "wt", encoding="utf-8") as fout:
            json.dump(state_dict_metadata, fout)

    def set_streaming_state_inplace(self, state: StreamingStateDict):
        """
        Set the streaming state in-place, including that of
        sub-modules using a flattened-state dict.
        """
        device = next(self.parameters()).device
        def _set(name: str, module: StreamingModule):
            _set_streaming_state_inplace(module._streaming_state, state, prefix=name, device=device)
        self._apply_named_streaming(_set)
        if state:
            raise RuntimeError(f"Some states were not consumed: {list(state.keys())}")

    def set_streaming_state(self, state: dict[str, Any]):
        """Set the streaming state, including that of sub-modules."""
        state = dict(state)

        def _set(name: str, module: StreamingModule):
            if name in state:
                module._streaming_state = state[name]
                state.pop(name)
            else:
                raise RuntimeError(f"Expected to find a streaming state for {name}.")

        self._apply_named_streaming(_set)
        if state:
            raise RuntimeError(f"Some states were not consumed: {list(state.keys())}")


@dataclass
class _NullState:
    pass

    def reset(self) -> None:
        pass


class StreamingContainer(StreamingModule[_NullState]):
    def _init_streaming_state(self, batch_size: int) -> _NullState:
        return _NullState()


@dataclass
class _StreamingAddState:
    previous_x: torch.Tensor | None = None
    previous_y: torch.Tensor | None = None

    def reset(self):
        self.previous_x = None
        self.previous_y = None


class StreamingAdd(StreamingModule[_StreamingAddState]):
    def _init_streaming_state(self, batch_size: int) -> _StreamingAddState:
        return _StreamingAddState()

    def forward(self, x: torch.Tensor, y: torch.Tensor):
        if self._streaming_state is None:
            return x + y
        else:
            prev_x = self._streaming_state.previous_x
            prev_y = self._streaming_state.previous_y
            if prev_x is not None:
                x = torch.cat([prev_x, x], dim=-1)
            if prev_y is not None:
                y = torch.cat([prev_y, y], dim=-1)
            m_l = min(x.shape[-1], y.shape[-1])
            self._streaming_state.previous_x = x[..., m_l:]
            self._streaming_state.previous_y = y[..., m_l:]
            return x[..., :m_l] + y[..., :m_l]


@dataclass
class _StreamingConvState:
    previous: torch.Tensor | None = None

    def reset(self):
        self.previous = None


class RawStreamingConv1d(torch.nn.Conv1d, StreamingModule[_StreamingConvState]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.padding[0] == 0, "Padding should be handled outside."
        assert (
            self.stride[0] <= self.kernel_size[0]
        ), "stride must be less than kernel_size."

    def _init_streaming_state(self, batch_size: int) -> _StreamingConvState:
        return _StreamingConvState()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        stride = self.stride[0]
        # Effective kernel size accounting for dilation.
        kernel = (self.kernel_size[0] - 1) * self.dilation[0] + 1
        if self._streaming_state is None:
            return super().forward(input)
        else:
            # Due to the potential overlap, we might have some cache of the previous time steps.
            previous = self._streaming_state.previous
            if previous is not None:
                input = torch.cat([previous, input], dim=-1)
            B, C, T = input.shape
            # We now compute the number of full convolution frames, i.e. the frames
            # that are ready to be computed.
            num_frames = max(0, int(math.floor((T - kernel) / stride) + 1))
            offset = num_frames * stride
            # We will compute `num_frames` outputs, and we are advancing by `stride`
            # for each of the frame, so we know the data before `stride * num_frames`
            # will never be used again.
            self._streaming_state.previous = input[..., offset:]
            if num_frames > 0:
                input_length = (num_frames - 1) * stride + kernel
                out = super().forward(input[..., :input_length])
            else:
                # Not enough data as this point to output some new frames.
                out = torch.empty(
                    B, self.out_channels, 0, device=input.device, dtype=input.dtype
                )
            return out


@dataclass
class _StreamingConvTrState:
    partial: torch.Tensor | None = None

    def reset(self):
        self.partial = None


class RawStreamingConvTranspose1d(
    torch.nn.ConvTranspose1d, StreamingModule[_StreamingConvTrState]
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.padding[0] == 0, "Padding should be handled outside."
        assert self.dilation[0] == 1, "No dilation for now"
        assert (
            self.stride[0] <= self.kernel_size[0]
        ), "stride must be less than kernel_size."
        assert self.output_padding[0] == 0, "Output padding not supported."

    def _init_streaming_state(self, batch_size: int) -> _StreamingConvTrState:
        return _StreamingConvTrState()

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore
        B, C, T = x.shape
        stride = self.stride[0]
        kernel = self.kernel_size[0]
        if self._streaming_state is None:
            return super().forward(x)
        else:
            if T == 0:
                return torch.empty(
                    B, self.out_channels, 0, device=x.device, dtype=x.dtype
                )
            out = super().forward(x)
            OT = out.shape[-1]
            partial = self._streaming_state.partial
            if partial is not None:
                # Due to the potential overlap, the rightmost output of the conv transpose is not
                # ready to be output, as it will receive contributions from the next input frames.
                # Here we recover those `partial` output frames. We know that the first time step
                # of the `partial` tensor corresponds to the first time step of `out` as anything
                # coming before the first time step of `out` would have been already flushed.
                PT = partial.shape[-1]
                if self.bias is not None:
                    out[..., :PT] += partial - self.bias[:, None]
                else:
                    out[..., :PT] += partial
            # The input is T, the output is S * (T - 1) + K.
            # The offset of the left of the next frame will be S * T
            # so everything between 0 and S * T is ready to be output, and we need
            # to keep in the internal state everything beyond that, i.e. S (T - 1) + K - S T = K - S
            invalid_steps = kernel - stride
            partial = out[..., OT - invalid_steps :]
            out = out[..., : OT - invalid_steps]
            self._streaming_state.partial = partial
            return out


def test():
    torch.manual_seed(1234)
    device = "cpu"
    if torch.cuda.is_available():
        # Avoid the cuda optimizations that would take place on single precision
        # floats for convolutions.
        torch.backends.cudnn.enabled = True
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        device = "cuda:0"

    kernel_sizes = [1, 3, 4, 8, 15, 16]
    strides = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    chin = 6
    chout = 12

    for kernel, stride in itertools.product(kernel_sizes, strides):
        if stride > kernel:
            continue
        conv = RawStreamingConv1d(chin, chout, kernel, stride).to(device)
        convtr = RawStreamingConvTranspose1d(chout, chin, kernel, stride).to(device)

        for length in [4, 8, 32, 54, 65, 128, 1043]:
            print(f"ksize {kernel} strides {stride} len {length}")
            if length < kernel:
                continue
            batch_size = 3
            x = torch.randn(batch_size, chin, length).to(device)
            y = conv(x)
            z = convtr(y)
            for chunk_size in [1, 3, 5, 8]:
                ys = []
                zs = []
                with conv.streaming(batch_size), convtr.streaming(batch_size):
                    for offset in range(0, length, chunk_size):
                        chunk = x[..., offset : offset + chunk_size]
                        ys.append(conv(chunk))
                        zs.append(convtr(ys[-1]))
                y_stream = torch.cat(ys, dim=-1)
                z_stream = torch.cat(zs, dim=-1)
                y = y[..., : y_stream.shape[-1]]
                z = z[..., : z_stream.shape[-1]]
                assert y.shape == y_stream.shape, (y.shape, y_stream.shape)
                delta = (y_stream - y).norm() / y.norm()
                assert delta <= 1e-6, delta
                num_frames = int((length - kernel) / stride) + 1
                assert num_frames == y_stream.shape[-1]

                assert z.shape == z_stream.shape, (z.shape, z_stream.shape)
                delta = (z_stream - z).norm() / z.norm()
                assert delta <= 1e-6, (delta, (z_stream - z).abs().mean(dim=(0, 1)))


if __name__ == "__main__":
    with torch.no_grad():
        test()
