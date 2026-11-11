from .spec import DesignSpec,Part,Program

def generated_spec(source:str,parameters:dict,report:dict,previous:DesignSpec)->DesignSpec:
    appearances={p.id:p for p in previous.parts if p.template=='custom'}
    parts=[]
    for entry in report['parts']:
        part=Part.model_validate({**entry['part'],'measurements':{key:entry[key] for key in ('volume_mm3','surface_area_mm2','solid_count','face_count','provenance','watertight','relative_density') if key in entry}});old=appearances.get(part.id)
        if old:
            part.name=old.name;part.color=old.color;part.material=old.material;part.enabled=old.enabled
        parts.append(part)
    if not any(p.enabled for p in parts):parts[0].enabled=True
    data=previous.model_dump(mode='json');data['parts']=[p.model_dump(mode='json') for p in parts]
    data['program']=Program(source=source,parameters=parameters,artifact_id=report['artifact_id'],asset_id=report.get('asset_id'),meshing=report.get('meshing')).model_dump(mode='json')
    data['revision']+=1;data['simulation']['approved_fingerprint']=None
    return DesignSpec.model_validate(data)

def model_summary(spec:DesignSpec,report:dict)->str:
    if spec.program:
        count=len(report['parts']);solids=sum(p.get('solid_count',1) for p in report['parts'])
        return f'Built and validated {count} generated part(s), {solids} solid(s), using Python and the CAD engine. The model is ready for inspection and export.'
    p=next(p for p in spec.parts if p.enabled)
    return f'Validated {p.name}: {p.params.length:g} × {p.params.width:g} × {p.params.height:g} mm. Review materials and boundary conditions before running an analysis.'
