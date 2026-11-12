import test from 'node:test';import assert from 'node:assert/strict';
import {shortcutFor,shortcuts}from'../scripts/viewer/shortcuts.mjs';import{clampPanel}from'../scripts/viewer/floating-panel.mjs';
const e=(key:string,extra:any={})=>({key,target:{tagName:'BODY'},...extra});
test('shortcuts distinguish shifted actions and system command keys',()=>{assert.equal(shortcutFor(e('F',{shiftKey:true})).id,'fullscreen');assert.equal(shortcutFor(e('f')).id,'fit');assert.equal(shortcutFor(e('k',{metaKey:true})).id,'commands');assert.equal(shortcutFor(e('k',{ctrlKey:true})).id,'commands');assert.equal(shortcutFor(e('g',{ctrlKey:true})),null);});
test('typing and native text shortcuts do not alter the model display',()=>{assert.equal(shortcutFor(e('g',{target:{tagName:'TEXTAREA'}})),null);assert.equal(shortcutFor(e('h',{target:{isContentEditable:true}})),null);assert.equal(shortcutFor(e('g',{altKey:true})),null);});
test('every documented shortcut has a unique binding and an action name',()=>{assert.equal(new Set(shortcuts.map(s=>[s.key,!!s.mod,!!s.shift].join(':'))).size,shortcuts.length);assert.ok(shortcuts.every(s=>s.name&&s.label));});
test('floating panels stay accessible after drag and viewport resize',()=>{assert.deepEqual(clampPanel(-100,2000,380,500,1000,800),{left:8,top:292});assert.deepEqual(clampPanel(800,80,366,900,390,844),{left:16,top:8});});
