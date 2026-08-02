"""Text-to-video via a diffusion video model (`diffusers`' text-to-video
pipelines, e.g. damo-vilab/text-to-video-ms-1.7b).

`torch`/`diffusers` import cleanly on this host as of the current
requirements.txt (see the comment there — this used to be blocked by
Windows Smart App Control; that's no longer reproducing). What this file
hasn't been run through is a full generation: the text-to-video model is a
multi-GB download and, on CPU, realistically minutes-to-hours for even a
handful of frames — substantially heavier than app/modules/image_gen's
single still image, which *was* run end-to-end as proof the underlying
torch/diffusers stack genuinely works here. This is the real pipeline
shape, gated the same way; see interpolation.py for the classical-CV
alternative (optical-flow frame interpolation) that runs fast on any host.
"""

from pathlib import Path


def check_available() -> None:
    try:
        import diffusers  # noqa: F401
        import torch  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Text-to-video needs `torch` and `diffusers`. If this raises "
            "on your host, see app/modules/video_gen/diffusion_pipeline.py "
            "and app/modules/rag/models.py for the Smart App Control "
            "background — it's a Windows Code Integrity policy, not a "
            "platform-wide limitation."
        ) from exc


def generate_video(prompt: str, num_frames: int, fps: int, output_path: str) -> str:
    check_available()

    import torch
    from diffusers import DiffusionPipeline
    from diffusers.utils import export_to_video

    pipe = DiffusionPipeline.from_pretrained(
        "damo-vilab/text-to-video-ms-1.7b", torch_dtype=torch.float32, variant="fp16"
    )
    pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

    frames = pipe(prompt, num_inference_steps=25, num_frames=num_frames).frames[0]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    export_to_video(frames, output_path, fps=fps)
    return output_path
