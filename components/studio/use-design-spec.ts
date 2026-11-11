'use client';
import {useCallback,useMemo,useReducer,useState} from 'react';
import {designFromSpec,replaceDesign,replaceStudy,specFromDesign,validateSpec,localSpecKey} from '@/lib/engineering/spec';
import type {DesignSpec} from '@/lib/engineering/spec';
import {presets} from '@/lib/engineering/model';
import type {Design} from '@/lib/engineering/model';
import type {Study} from '@/lib/engineering/analysis';
type State={past:DesignSpec[];present:DesignSpec;future:DesignSpec[]};
type Action={type:'edit';apply:(s:DesignSpec)=>DesignSpec}|{type:'restore';spec:DesignSpec}|{type:'undo'}|{type:'redo'};
function reduce(s:State,a:Action):State{
  if(a.type==='restore')return {past:[],present:validateSpec(a.spec),future:[]};
  if(a.type==='undo'){if(!s.past.length)return s;return {past:s.past.slice(0,-1),present:s.past[s.past.length-1],future:[s.present,...s.future].slice(0,50)};}
  if(a.type==='redo'){if(!s.future.length)return s;return {past:[...s.past,s.present].slice(-50),present:s.future[0],future:s.future.slice(1)};}
  const next=a.apply(s.present);if(localSpecKey(next)===localSpecKey(s.present))return s;
  return {past:[...s.past,s.present].slice(-50),present:next,future:[]};
}
export function useDesignSpec(){
  const [state,dispatch]=useReducer(reduce,{past:[],present:specFromDesign(presets.heatsink),future:[]});const spec=state.present;const [selectedId,setSelectedId]=useState('main');const selectedPart=spec.parts.find(p=>p.id===selectedId)??spec.parts.find(p=>p.enabled)!;
  const design=useMemo(()=>designFromSpec(spec,selectedPart.id),[spec.parts,selectedPart.id]);const study=spec.simulation.study;
  const setDesign=useCallback((value:Design|((d:Design)=>Design))=>dispatch({type:'edit',apply:s=>replaceDesign(s,typeof value==='function'?value(designFromSpec(s,selectedPart.id)):value,selectedPart.id)}),[selectedPart.id]);
  const setStudy=useCallback((value:Study|((s:Study)=>Study))=>dispatch({type:'edit',apply:s=>replaceStudy(s,typeof value==='function'?value(s.simulation.study):value)}),[]);
  const setSpec=useCallback((value:DesignSpec)=>dispatch({type:'edit',apply:s=>({...validateSpec(value),revision:Math.max(s.revision+1,value.revision),simulation:{...value.simulation,approved_fingerprint:null}})}),[]);
  return {spec,selectedPart,selectPart:useCallback((id:string)=>setSelectedId(id),[]),design,study,setDesign,setStudy,setSpec,restoreSpec:useCallback((spec:DesignSpec)=>dispatch({type:'restore',spec}),[]),undo:()=>dispatch({type:'undo'}),redo:()=>dispatch({type:'redo'}),canUndo:!!state.past.length,canRedo:!!state.future.length,historyCount:state.past.length};
}
