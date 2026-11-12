"""Discoverable MCP tools for interactive workflows."""
from typing import Any, Literal, Annotated
from pydantic import Field, StrictFloat, StrictInt, StrictStr
from mcp.server.mcpserver import Context
from .view_settings import ViewSettings
from .interactive import view_command, parameter_command

NAMES={'list_commands','describe_command','control_view','parameter_configuration','preview_parameters','apply_configuration'}

def dispatch(engine,name,args,cancel_event):
    if name in ('list_commands','describe_command'):
        catalog=getattr(engine,'command_catalog',{})
        def permitted(command):
            try:engine.authorize(command,{'model_id':args.get('model_id')});return True
            except Exception:return False
        if name=='list_commands':return {'commands':[{'name':k,'description':v['description'].split('\n')[0],'read_only':v['read_only']} for k,v in catalog.items() if permitted(k)],'execution':'Call the named MCP tool directly; describe_command returns its exact input schema.'}
        command=args['command']
        if command not in catalog or not permitted(command):raise ValueError('Command is unknown or unavailable in this task.')
        return catalog[command]
    if name=='control_view':
        args=dict(args);args.pop('model_id',None);return view_command(engine.projects,**args)
    args={**args,'key':args['model_id']};del args['model_id']
    if name=='preview_parameters':args['action']='preview'
    if name=='apply_configuration':args['action']='apply'
    result=parameter_command(engine.projects,**args,cancel_event=cancel_event)
    return engine.result(result) if name=='apply_configuration' else result


def register(server,engine,execute,read,write):
    @server.tool(annotations=read)
    def list_commands(model_id:str|None=None)->dict[str,Any]:
        """Discover installed AI tools and their capabilities. In Ask AI, pass the active model_id to list only tools permitted for this task. Call a tool by its own name; no shell commands are accepted."""
        return engine.call('list_commands',{'model_id':model_id})
    @server.tool(annotations=read)
    def describe_command(command:str,model_id:str|None=None)->dict[str,Any]:
        """Return the exact current MCP input schema and description for a permitted tool."""
        return engine.call('describe_command',{'command':command,'model_id':model_id})
    @server.tool(annotations=write)
    def control_view(model_id:str,action:Literal['get','update','save','list','restore','delete']='get',settings:ViewSettings|None=None,name:str|None=None,expected_view_revision:Annotated[StrictInt,Field(ge=0)]|None=None)->dict[str,Any]:
        """AI viewer control and named view bookmarks, without CAD revisions. Update merges supplied settings: hidden part IDs, cut x/y/z with slice 0–100, explode 0–100, projection, display colors, grid, camera and more. Camera = [eyeX,eyeY,eyeZ,targetX,targetY,targetZ] in viewer mm (CAD X,Z,-Y). Get first and supply expected_view_revision to avoid overwriting concurrent changes. Save/restore/delete use name; saved views refuse stale geometry. Active viewer refreshes automatically outside Simulation/history."""
        return engine.call('control_view',dict(key=model_id,model_id=model_id,action=action,settings=settings.model_dump(mode='json',exclude_unset=True) if settings else None,name=name,expected_view_revision=expected_view_revision))
    @server.tool(annotations=write)
    def parameter_configuration(model_id:str,action:Literal['list','save','delete']='list',name:str|None=None,parameters:dict[str,StrictFloat|StrictStr]|None=None,expected_revision:Annotated[StrictInt,Field(ge=1)]|None=None)->dict[str,Any]:
        """Save/list/delete named parameter configurations without rebuilding or adding CAD revisions. Values may use bounded arithmetic expressions with existing parameter names, parentheses and + - * /; scalar values are in CAD mm where length-valued. No Python eval, functions or implicit units. Saving resolves expressions to numeric snapshots. Use preview_parameters then apply_configuration to rebuild. Up to 30 configurations per model."""
        return engine.call('parameter_configuration',dict(model_id=model_id,action=action,name=name,parameters=parameters,expected_revision=expected_revision))
    @server.tool(annotations=read)
    async def preview_parameters(model_id:str,parameters:dict[str,StrictFloat|StrictStr],ctx:Context,expected_revision:Annotated[StrictInt,Field(ge=1)]|None=None)->dict[str,Any]:
        """Rebuild candidate parameters in a disposable isolated project and return actual bounds and volumes. Preserves original source, CAD, history, imported inputs and configurations even on failure. Supports bounded scalar arithmetic expressions. No preview files or revisions are added to the real project; run update_parameters to commit after inspection."""
        return await execute('preview_parameters',dict(model_id=model_id,parameters=parameters,expected_revision=expected_revision),ctx)
    @server.tool(annotations=write)
    async def apply_configuration(model_id:str,name:str,ctx:Context,expected_revision:Annotated[StrictInt,Field(ge=1)])->dict[str,Any]:
        """Rebuild a named parameter configuration against the expected current CAD revision. Commits once only after successful sandbox geometry validation. Failed or stale builds preserve the current model. Validate dimensions and inspect a snapshot afterward."""
        return await execute('apply_configuration',dict(model_id=model_id,name=name,expected_revision=expected_revision),ctx)
    engine.command_catalog={t.name:{'name':t.name,'description':t.description or '', 'input_schema':t.parameters,'read_only':bool(t.annotations and t.annotations.read_only_hint)} for t in server._tool_manager.list_tools()}
