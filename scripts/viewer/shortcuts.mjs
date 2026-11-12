/** Shared shortcut registry used by the actual handlers and Tutorial. */
export const shortcuts=[
 {id:'commands',key:'k',mod:true,label:'Ctrl/Cmd+K',name:'Commands and saved views'},
 {id:'review',key:'r',label:'R',name:'Open design review'},
 {id:'fit',key:'f',label:'F',name:'Zoom to fit'},
 {id:'fullscreen',key:'f',shift:true,label:'Shift+F',name:'Full screen / compact screen'},
 {id:'grid',key:'g',label:'G',name:'Toggle grid'},
 {id:'ask',key:'a',label:'A',name:'Open Ask AI'},
 {id:'measure',key:'m',label:'M',name:'Measure two points'},
 {id:'edge',key:'e',label:'E',name:'Select edges'},
 {id:'part',key:'v',label:'V',name:'Select parts'},
 {id:'isolate',key:'i',label:'I',name:'Isolate selected parts'},
 {id:'hide',key:'h',label:'H',name:'Hide selected parts'},
 {id:'show',key:'h',shift:true,label:'Shift+H',name:'Show all parts'},
 {id:'settings',key:'s',label:'S',name:'Open / close Settings'},
 {id:'draw',key:'d',label:'D',name:'Open / close Draw / annotate'},
 {id:'iso',key:'1',label:'1',name:'Isometric view'},
 {id:'front',key:'2',label:'2',name:'Front view'},
 {id:'top',key:'3',label:'3',name:'Top view'},
 {id:'right',key:'4',label:'4',name:'Right view'},
 {id:'tutorial',key:'?',shift:true,label:'?',name:'Open Tutorial / shortcut help'},
];
export function shortcutFor(event){if(event.altKey)return null;const editing=event.target?.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(event.target?.tagName||'');return shortcuts.find(s=>s.key===event.key.toLowerCase()&&Boolean(s.mod)===Boolean(event.ctrlKey||event.metaKey)&&(s.key==='?'||Boolean(s.shift)===Boolean(event.shiftKey))&&(!editing||s.mod))||null;}
export function installShortcuts(actions,{escape=()=>false,enabled=()=>true}={}){document.addEventListener('keydown',e=>{if(e.defaultPrevented)return;if(e.key==='Escape'&&escape()){e.preventDefault();e.stopImmediatePropagation();return;}const shortcut=shortcutFor(e);if(!shortcut||!enabled(shortcut.id)||!actions[shortcut.id])return;e.preventDefault();actions[shortcut.id]();},true);}
