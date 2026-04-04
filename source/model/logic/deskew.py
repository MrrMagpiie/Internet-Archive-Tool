from pathlib import Path

def deskew_task(in_file, out_file, queue):
    """Thread task deskew: returns status and angle of adjustment in queue"""
    try:
    
            angle = deskew_image(in_file, out_file)
            queue.put({"status": "success", "angle": angle})
        
    except KeyboardInterrupt as e:
        pass

    except Exception as e:
        queue.put({"status": "error", "error": str(e)})


def deskew_image(in_file, out_file):
    """Automatic Image Deskewing: returns angle of adjustment"""
    try:
        from wand.image import Image
        from wand.color import Color
        
        with Image(filename=str(in_file)) as img:
            img.background_color = Color('transparent')
            
            with img.clone() as deskewed_img:
                deskewed_img.deskew(0.40 * deskewed_img.quantum_range)
                
                angle_str = deskewed_img.artifacts.get('deskew:angle', '0')
                angle = float(angle_str)
                
                if abs(angle) < 1.0:
                    img.save(filename=str(out_file))
                    return 0.0
                else:
                    deskewed_img.save(filename=str(out_file))
                    return angle

    except Exception as e:
        raise
        
        
        