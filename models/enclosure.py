"""Open enclosure and separate lid. The assembly origin is centered in X/Y; Z is up."""
import build123d as bd

def build(params):
    length=params['length'];width=params['width'];height=params['height'];wall=params['wall']
    align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)
    outside=bd.Box(length,width,height,align=align)
    cavity=bd.Pos(0,0,wall)*bd.Box(length-2*wall,width-2*wall,height,align=align)
    base=outside-cavity
    lid=bd.Pos(0,0,height+params['lid_gap'])*bd.Box(length,width,wall,align=align)
    return {'base':base,'lid':lid}
