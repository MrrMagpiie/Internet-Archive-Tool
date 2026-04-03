from pathlib import Path

def deskew_task(in_file, out_file, queue):
    """Thread task deskew: returns status and angle of adjustment in queue"""
    try:
        from wand.image import Image
        from wand.color import Color
        
        with Image(filename=str(in_file)) as img:
            img.background_color = Color('transparent')
            img.deskew(0.40 * img.quantum_range)
            img.save(filename=str(out_file))
            angle = img.artifacts.get('deskew:angle', 0)
            
            queue.put({"status": "success", "angle": angle})
        
    except KeyboardInterrupt as e:
        pass

    except Exception as e:
        queue.put({"status": "error", "error": str(e)})
        
def deskew_image(in_file, out_file, queue = None):
    """Automatic Image Deskewing: returns angle of adjustment"""
    try:
        from wand.image import Image
        from wand.color import Color
        
        with Image(filename=str(in_file)) as img:
            img.background_color = Color('transparent')
            img.deskew(0.40 * img.quantum_range)
            img.save(filename=str(out_file))
            angle = img.artifacts.get('deskew:angle', 0)
            
            return angle

    except Exception as e:
        raise
        
        
        