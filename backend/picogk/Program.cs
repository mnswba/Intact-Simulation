// SPDX-License-Identifier: Apache-2.0
using System.Numerics;
using System.Text.Json;
using PicoGK;
if(args.Length!=2)throw new ArgumentException("Expected request JSON and STL output paths.");
var request=JsonDocument.Parse(File.ReadAllText(args[0])).RootElement;
float voxel=request.GetProperty("voxel_mm").GetSingle();
using var library=new Library(voxel);
var field=new Tpms(request);
using var voxels=new Voxels(library,field,field.Bounds);
using var mesh=new Mesh(voxels);
mesh.SaveToStlFile(args[1]);
Console.WriteLine("PicoGK TPMS voxel mesh completed.");
sealed class Tpms:IImplicit{
 readonly double cell,wall,gradient;readonly Vector3 size;readonly string family;
 public BBox3 Bounds{get;}
 public Tpms(JsonElement r){var s=r.GetProperty("size").EnumerateArray().Select(x=>x.GetSingle()).ToArray();size=new Vector3(s[0],s[1],s[2]);cell=r.GetProperty("cell_size").GetDouble();wall=r.GetProperty("thickness_mm").GetDouble();gradient=r.GetProperty("gradient").GetDouble();family=r.GetProperty("family").GetString()!;float pad=r.GetProperty("voxel_mm").GetSingle()*2;Bounds=new BBox3(-size/2-new Vector3(pad),size/2+new Vector3(pad));}
 double F(Vector3 p){double k=2*Math.PI/cell,x=p.X*k,y=p.Y*k,z=p.Z*k,sx=Math.Sin(x),sy=Math.Sin(y),sz=Math.Sin(z),cx=Math.Cos(x),cy=Math.Cos(y),cz=Math.Cos(z);return family switch{
 "gyroid"=>sx*cy+sy*cz+sz*cx,
 "schwarz_p"=>cx+cy+cz,
 "diamond"=>sx*sy*sz+sx*cy*cz+cx*sy*cz+cx*cy*sz,
 "neovius"=>3*(cx+cy+cz)+4*cx*cy*cz,
 "lidinoid"=>.5*(Math.Sin(2*x)*cy*sz+Math.Sin(2*y)*cz*sx+Math.Sin(2*z)*cx*sy)-.5*(Math.Cos(2*x)*Math.Cos(2*y)+Math.Cos(2*y)*Math.Cos(2*z)+Math.Cos(2*z)*Math.Cos(2*x))+.15,
 "split_p"=>1.1*(Math.Sin(2*x)*sy*cz+Math.Sin(2*y)*sz*cx+Math.Sin(2*z)*sx*cy)-.2*(Math.Cos(2*x)*Math.Cos(2*y)+Math.Cos(2*y)*Math.Cos(2*z)+Math.Cos(2*z)*Math.Cos(2*x))-.4*(Math.Cos(2*x)+Math.Cos(2*y)+Math.Cos(2*z)),
 _=>throw new ArgumentException("Unknown TPMS family")};}
 public float fSignedDistance(in Vector3 p){float delta=(float)Math.Min(cell*.001,.01);double dx=(F(p+new Vector3(delta,0,0))-F(p-new Vector3(delta,0,0)))/(2*delta),dy=(F(p+new Vector3(0,delta,0))-F(p-new Vector3(0,delta,0)))/(2*delta),dz=(F(p+new Vector3(0,0,delta))-F(p-new Vector3(0,0,delta)))/(2*delta);double shell=Math.Abs(F(p))/Math.Max(Math.Sqrt(dx*dx+dy*dy+dz*dz),1e-8)-wall*(1+gradient*2*p.Z/size.Z)/2;Vector3 q=Vector3.Abs(p)-size/2;double box=Vector3.Max(q,Vector3.Zero).Length()+Math.Min(Math.Max(q.X,Math.Max(q.Y,q.Z)),0);return (float)Math.Max(shell,box);}
}
