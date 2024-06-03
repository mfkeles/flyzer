from imageio_ffmpeg import write_frames


def initiate_videowriter(full_file_name, frame_width, frame_height, fps):
    while True:
        try:
            writer = write_frames(
                full_file_name,
                [frame_width, frame_height],  # size [W,H]
                fps=fps,
                quality=6,
                macro_block_size=4,
                codec='libx264',
                pix_fmt_in='gray',  # "bayer_bggr8", "gray", "rgb24", "bgr0", "yuv420p"
                ffmpeg_log_level='warning',  # "warning", "quiet", "info"
                input_params=["-an"],  # "-an" no audio
            )
            writer.send(None)  # Initialize the generator
            writing = True
            break
        except Exception as e:
            print("Caught exception at writer.py OpenWriter: {}".format(e))
            raise
            break

    return writer
