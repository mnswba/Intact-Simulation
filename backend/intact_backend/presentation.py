"""Measured, professional concept-review slides; never invented engineering results."""
import base64,io,math,json,re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image
from .edit_requests import EditRequests

NAVY='15344B';BLUE='226DA4';INK='20364D';MUTED='5B6E7D';LIGHT='EDF3F7';WHITE='FFFFFF'

def build_deck(projects,record,data,target):
 images=data.get('images',[])
 if not isinstance(images,list) or not 1<=len(images)<=5:raise ValueError('Provide one to five genuine viewport images.')
 if sum(len(i.get('data_url','')) for i in images if isinstance(i,dict))>20*1024*1024:raise ValueError('Slide images exceed the total size limit.')
 purpose=data.get('purpose','Concept design review');notes=data.get('review_notes','')
 if not isinstance(purpose,str) or not 1<=len(purpose.strip())<=160 or not isinstance(notes,str) or len(notes)>2000:raise ValueError('Use a purpose of 1–160 characters and review notes of at most 2,000 characters.')
 decoded=[]
 for item in images:
  image=EditRequests(projects).image(item);raw=base64.b64decode(image['data_url'].split(',',1)[1])
  try:
   im=Image.open(io.BytesIO(raw));width,height=im.size
   if width*height>24000000:raise ValueError('Slide image exceeds the 24-megapixel limit.')
   im.verify()
  except (OSError,ValueError) as exc:raise ValueError('Slide image is invalid or truncated.') from exc
  decoded.append((image['name'],raw,width,height))
 prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5);prs.core_properties.title=record['name'];prs.core_properties.subject=purpose.strip();prs.core_properties.author='Intact Simulation'
 def rect(slide,x,y,w,h,color):
  shape=slide.shapes.add_shape(1,Inches(x),Inches(y),Inches(w),Inches(h));shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(color);shape.line.fill.background();return shape
 def text(slide,value,x,y,w,h,size=18,color=INK,bold=False):
  box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=box.text_frame;tf.word_wrap=True
  for i,line in enumerate(str(value).split('\n')):
   p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='Arial';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color);p.space_after=Pt(9)
  return box
 def page(title,dark=False):
  slide=prs.slides.add_slide(prs.slide_layouts[5]);slide.background.fill.solid();slide.background.fill.fore_color.rgb=RGBColor.from_string(NAVY if dark else WHITE)
  text(slide,'INTACT SIMULATION  /  DESIGN REVIEW',.45,.2,10,.3,10,WHITE if dark else BLUE,True)
  rect(slide,.45,.72,12.43,.025,BLUE);heading=slide.shapes.title;heading.text=title;heading.left=Inches(.55);heading.top=Inches(.87);heading.width=Inches(12.2);heading.height=Inches(.8)
  for paragraph in heading.text_frame.paragraphs:paragraph.font.name='Arial';paragraph.font.size=Pt(26 if len(title)>65 else 28);paragraph.font.bold=True;paragraph.font.color.rgb=RGBColor.from_string(WHITE if dark else INK)
  text(slide,f"{record['name'][:65]}  •  Revision {record['spec']['revision']}",.55,7.06,10,.25,9,WHITE if dark else MUTED);text(slide,str(len(prs.slides)),12.2,7.06,.5,.25,9,WHITE if dark else MUTED)
  return slide
 def picture(slide,image,x,y,w,h):
  _,raw,width,height=image;scale=min(w/width,h/height);actual_w=width*scale;actual_h=height*scale
  slide.shapes.add_picture(io.BytesIO(raw),Inches(x+(w-actual_w)/2),Inches(y+(h-actual_h)/2),width=Inches(actual_w),height=Inches(actual_h))
 parts=record['spec']['parts'];low=[min(p['position'][i]-(p['params'][('length','width')[i]]/2 if i<2 else 0) for p in parts) for i in range(3)];high=[max(p['position'][i]+(p['params'][('length','width')[i]]/2 if i<2 else p['params']['height']) for p in parts) for i in range(3)];envelope=' × '.join(f'{b-a:,.2f}' for a,b in zip(low,high))+' mm'
 audit=record['geometry'].get('audit',{});design=audit.get('design_verification',{});design_status=design.get('status','not evaluated') if isinstance(design,dict) else 'not evaluated';native=record['geometry']['engine']!='implicit_mesh'
 if record.get('engineering',{}).get('diagnostics',{}).get('needs_rebuild'):design_status='rebuild_required'
 def status_label(value):return {'rebuild_required':'Rebuild required','not_specified':'Not supplied','not_evaluated':'Not evaluated','passed':'Passed','failed':'Requires correction','unverified':'Further verification required'}.get(value,str(value).replace('_',' ').capitalize())
 cover=page(record['name'],True);text(cover,purpose.strip(),.6,1.8,4.4,1.2,24,WHITE);text(cover,f"{len(parts)} saved components\nEnvelope: {envelope}\n{'Native B-rep geometry' if native else 'Sampled mesh geometry'}",.6,3.25,4.35,1.9,17,WHITE);rect(cover,5.2,1.8,7.55,4.75,WHITE);picture(cover,decoded[1] if len(decoded)>1 else decoded[0],5.3,1.9,7.35,4.55)
 cover.notes_slide.notes_text_frame.text='Concept review based on saved geometry. No manufacturing approval or physical performance certification is implied.'
 for name,image,width,height in decoded:
  slide=page(name[:110]);picture(slide,(name,image,width,height),.55,1.65,12.2,4.95);text(slide,{'Current design review':'Saved review display: camera, section planes and component visibility provide discussion context.','Assembly overview':'Assembled configuration. Review component relationships and overall proportions.','Front elevation':'Front elevation · parallel projection. Review alignment and interface positions.','Plan view':'Plan view · parallel projection. Review layout, spacing and mounting patterns.','Right elevation':'Right elevation · parallel projection. Review thickness and vertical placement.'}.get(name,'Review capture. Consult the source model and analysis report for dimensions, assumptions and verification.'),.65,6.65,12,.3,11,MUTED)
  slide.notes_slide.notes_text_frame.text=f"Saved revision {record['spec']['revision']}. View: {name}. Inspect dimensions and acceptance criteria before making design decisions."
 summary=page('Design evidence and review decisions');text(summary,f"Geometry checks: {status_label(audit.get('status','not evaluated'))}\nDesign acceptance criteria: {status_label(design_status)}\nEnvelope: {envelope}\nNamed components: {len(parts)}",.65,1.8,5.7,3.1,20)
 text(summary,'Discussion priorities\n1. Confirm critical dimensions and interfaces.\n2. Compare alternatives before committing edits.\n3. Record assumptions and required verification.',6.75,1.8,5.7,3.2,19)
 text(summary,'Physical performance and manufacturing suitability require their own evidence. A missing design criterion is not a verification pass.',.65,5.4,12,1,15,MUTED)
 if notes.strip():
  slide=page('Review notes and next steps');text(slide,notes.strip(),.7,1.85,11.9,4.9,20);slide.notes_slide.notes_text_frame.text='User/AI-supplied review notes; verify statements against the model and analysis evidence.'
 analysis_id=data.get('analysis_report_id')
 if analysis_id:
  if not isinstance(analysis_id,str) or not re.fullmatch('[a-f0-9]{32}',analysis_id):raise ValueError('Invalid analysis report identifier.')
  analysis_path=projects.root/'engineering'/analysis_id/'report.json'
  if not analysis_path.is_file():raise ValueError('Analysis report not found.')
  analysis=json.loads(analysis_path.read_text())
  if analysis.get('model_id')!=record['model_id'] or analysis.get('artifact_id')!=record['spec']['program']['artifact_id']:raise ValueError('The analysis belongs to different or stale geometry. Run or choose an analysis for the current model.')
  if analysis.get('kind') not in ('thermal','structural','stokes'):raise ValueError('This deck supports saved thermal, structural and creeping-flow analysis reports.')
  slide=page('Saved analysis evidence');field=analysis['field_name'];lo=analysis['minimum'];hi=analysis['maximum']
  text(slide,f"Analysis: {analysis['kind'].capitalize()}\nComponent: {analysis.get('study_definition',{}).get('part_id','Not recorded')}\nSource revision: {analysis['revision']}\nField: {field}\nRange: {lo:.6g} … {hi:.6g}\nMesh: {analysis['vertices']:,} nodes / {analysis['tetrahedra']:,} tetrahedra",.65,1.8,6,3.9,19)
  text(slide,f"Residual: {analysis['relative_residual']:.3e}\nBalance error: {analysis['relative_balance_error']:.3e}\nMesh refinement: {'Passed' if analysis.get('convergence',{}).get('passed') else 'Needs review'}\nReported field: {'Numerically verified' if analysis.get('verified') else 'Unverified'}",6.9,1.8,5.7,3.3,18)
  text(slide,analysis.get('scope','Consult the saved analysis report for assumptions and applicability.'),.65,5.65,12,1,13,MUTED)
  study=analysis.get('study_definition',{});input_notes=[]
  for key,label,unit in [('conductivity_w_mk','Thermal conductivity','W/(m K)'),('young_modulus_pa','Young modulus','Pa'),('poisson_ratio','Poisson ratio',''),('viscosity_pa_s','Dynamic viscosity','Pa s'),('density_kg_m3','Density','kg/m³'),('force_n','Default force vector','N'),('pressure_drop_pa','Pressure drop','Pa'),('mesh_size_mm','Requested mesh size','mm')]:
   relevant={'thermal':{'conductivity_w_mk','mesh_size_mm'},'structural':{'young_modulus_pa','poisson_ratio','force_n','mesh_size_mm'},'stokes':{'viscosity_pa_s','density_kg_m3','pressure_drop_pa','mesh_size_mm'}}[analysis['kind']]
   if key in relevant and key in study and not (key=='force_n' and study.get('boundary_conditions')):input_notes.append(label+': '+str(study[key])+' '+unit)
  slide.notes_slide.notes_text_frame.text='Actual saved solver report '+analysis_id+'\n'+study.get('user_request','')+'\n'+'\n'.join(input_notes)+'\n'+analysis.get('unit_system','')+'\nField verification: '+str(analysis.get('verified_fields',{}))
 # Paginate actual data instead of dropping components or shrinking to unreadable text.
 for start in range(0,len(parts),12):
  chunk=parts[start:start+12];slide=page('Saved component register'+(f' · {start+1}–{start+len(chunk)}' if len(parts)>12 else ''));table=slide.shapes.add_table(len(chunk)+1,4,Inches(.6),Inches(1.75),Inches(12.1),Inches(.36*(len(chunk)+1))).table
  for i,w in enumerate([5.0,3.6,1.8,1.7]):table.columns[i].width=Inches(w)
  rows=[['Component','Envelope X × Y × Z · mm','Volume · mm³','Material label']]+[[p['name'], ' × '.join(f"{p['params'][k]:.2f}" for k in ('length','width','height')),f"{p['measurements']['volume_mm3']:,.1f}",p.get('material','unspecified')] for p in chunk]
  for r,row in enumerate(rows):
   for c,value in enumerate(row):
    cell=table.cell(r,c);cell.text=str(value);cell.fill.solid();cell.fill.fore_color.rgb=RGBColor.from_string(NAVY if r==0 else LIGHT if r%2 else WHITE)
    for paragraph in cell.text_frame.paragraphs:paragraph.font.name='Arial';paragraph.font.size=Pt(12 if r==0 else 11);paragraph.font.color.rgb=RGBColor.from_string(WHITE if r==0 else INK);paragraph.font.bold=r==0
  text(slide,'All saved named instances are listed, including display-hidden parts. Material labels are not supplier-certified properties. Volumes are per component, not an assembly union.',.65,6.7,12,.3,10,MUTED)
 prs.save(target)
 return {'slides':len(prs.slides),'image_count':len(decoded),'minimum_image_pixels':min(w*h for _,_,w,h in decoded),'scope':'Measured geometry and genuine review captures, with traceable revision, audit status and paginated components; no invented simulation or approval.'}
