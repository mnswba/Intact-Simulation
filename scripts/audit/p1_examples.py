"""Small public JSON examples for the constrained-design tools."""
CIRCLE={'id':'outline','geometry':[{'id':'circle','kind':'circle','radius':20}], 'constraints':[{'id':'diameter','kind':'diameter','entities':['circle'],'value':{'parameter':'diameter'}},{'id':'cx','kind':'distance_x','entities':['circle'],'points':[3],'value':0},{'id':'cy','kind':'distance_y','entities':['circle'],'points':[3],'value':0}]}
PAD={'id':'pad','kind':'extrude','part_id':'disk','sketch_id':'outline','params':{'height':{'parameter':'thickness'}}}
