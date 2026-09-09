// ingest test: run fontasy_fork's raster->vector color-zone pipeline over whole
// illustrations (not glyph grids). core functions below are extracted verbatim
// from kqrla/fontasy_fork web/index.html (MIT, same-project-team, perms
// confirmed). adaptations for full-image ingestion are marked INGEST.
//
// usage: node scripts/fork_ingest_test.mjs <rawrgba> <w> <h> <k> <outsvg> <outjson>

import { readFileSync, writeFileSync } from 'fs';

// ---------- verbatim from fontasy_fork ----------
function toGray(d,w,h){const g=new Uint8Array(w*h);for(let i=0;i<g.length;i++){const j=i*4;g[i]=Math.round(.299*d[j]+.587*d[j+1]+.114*d[j+2])}return g}
function gaussianBlur(g,w,h,r){if(r<=0)return g;const sz=r*2+1,k=new Float32Array(sz);let s=0;for(let i=0;i<sz;i++){const x=i-r;k[i]=Math.exp(-(x*x)/(2*.36*r*r));s+=k[i]}for(let i=0;i<sz;i++)k[i]/=s;const t=new Uint8Array(w*h),o=new Uint8Array(w*h);for(let y=0;y<h;y++)for(let x=0;x<w;x++){let v=0;for(let i=0;i<sz;i++)v+=g[y*w+Math.min(w-1,Math.max(0,x+i-r))]*k[i];t[y*w+x]=Math.round(v)}for(let y=0;y<h;y++)for(let x=0;x<w;x++){let v=0;for(let i=0;i<sz;i++)v+=t[Math.min(h-1,Math.max(0,y+i-r))*w+x]*k[i];o[y*w+x]=Math.round(v)}return o}
function labelComponents(b,w,h){const L=new Int32Array(w*h);let n=1;const st=[];for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x;if(b[i]&&!L[i]){const l=n++;st.push(i);while(st.length){const j=st.pop();if(L[j])continue;L[j]=l;const cy=(j/w)|0,cx=j%w;if(cx>0&&b[j-1]&&!L[j-1])st.push(j-1);if(cx<w-1&&b[j+1]&&!L[j+1])st.push(j+1);if(cy>0&&b[j-w]&&!L[j-w])st.push(j-w);if(cy<h-1&&b[j+w]&&!L[j+w])st.push(j+w)}}}return{labels:L,count:n-1}}
function getBounds(L,w,h,c){const B=[];for(let i=0;i<=c;i++)B.push({x1:w,y1:h,x2:0,y2:0,area:0});for(let y=0;y<h;y++)for(let x=0;x<w;x++){const l=L[y*w+x];if(!l)continue;const b=B[l];if(x<b.x1)b.x1=x;if(x>b.x2)b.x2=x;if(y<b.y1)b.y1=y;if(y>b.y2)b.y2=y;b.area++}return B}
function mooreTrace(b,w,h,sx,sy){const dirs=[[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1]];const ct=[];let x=sx,y=sy,dir=6,steps=0;do{ct.push([x,y]);let found=false;for(let i=0;i<8;i++){const d=(dir+5+i)%8,nx=x+dirs[d][0],ny=y+dirs[d][1];if(nx>=0&&nx<w&&ny>=0&&ny<h&&b[ny*w+nx]){x=nx;y=ny;dir=d;found=true;break}}if(!found)break;if(++steps>w*h)break}while(x!==sx||y!==sy);return ct}
function simplify(pts,eps){if(pts.length<3)return pts;let mx=0,mi=0;const[sx,sy]=pts[0],[ex,ey]=pts[pts.length-1],dx=ex-sx,dy=ey-sy,ls=dx*dx+dy*dy;for(let i=1;i<pts.length-1;i++){let d;if(ls===0)d=Math.hypot(pts[i][0]-sx,pts[i][1]-sy);else{const t=Math.max(0,Math.min(1,((pts[i][0]-sx)*dx+(pts[i][1]-sy)*dy)/ls));d=Math.hypot(pts[i][0]-(sx+t*dx),pts[i][1]-(sy+t*dy))}if(d>mx){mx=d;mi=i}}if(mx>eps){const l=simplify(pts.slice(0,mi+1),eps),r=simplify(pts.slice(mi),eps);return l.slice(0,-1).concat(r)}return[pts[0],pts[pts.length-1]]}
function floodFillBg(b,w,h){const v=new Uint8Array(w*h),st=[];for(let x=0;x<w;x++){if(!b[x])st.push(x);if(!b[(h-1)*w+x])st.push((h-1)*w+x)}for(let y=0;y<h;y++){if(!b[y*w])st.push(y*w);if(!b[y*w+w-1])st.push(y*w+w-1)}while(st.length){const i=st.pop();if(v[i])continue;v[i]=1;const cy=(i/w)|0,cx=i%w;if(cx>0&&!b[i-1]&&!v[i-1])st.push(i-1);if(cx<w-1&&!b[i+1]&&!v[i+1])st.push(i+1);if(cy>0&&!b[i-w]&&!v[i-w])st.push(i-w);if(cy<h-1&&!b[i+w]&&!v[i+w])st.push(i+w)}return v}
function findHoles(b,w,h,bg){const holes=[],v=new Uint8Array(w*h);for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++){const i=y*w+x;if(!b[i]&&!bg[i]&&!v[i]){const hole=[],st=[i];while(st.length){const j=st.pop();if(v[j])continue;v[j]=1;hole.push(j);const cy=(j/w)|0,cx=j%w;if(cx>0&&!b[j-1]&&!v[j-1])st.push(j-1);if(cx<w-1&&!b[j+1]&&!v[j+1])st.push(j+1);if(cy>0&&!b[j-w]&&!v[j-w])st.push(j-w);if(cy<h-1&&!b[j+w]&&!v[j+w])st.push(j+w)}if(hole.length>4)holes.push(hole)}}return holes}
function polyToBezier(pts){if(pts.length<2)return'';let d=`M ${pts[0][0]} ${pts[0][1]} `;if(pts.length===2)return d+`L ${pts[1][0]} ${pts[1][1]} Z`;for(let i=0;i<pts.length;i++){const p0=pts[(i-1+pts.length)%pts.length],p1=pts[i],p2=pts[(i+1)%pts.length],p3=pts[(i+2)%pts.length],t=.3;d+=`C ${p1[0]+(p2[0]-p0[0])*t/3} ${p1[1]+(p2[1]-p0[1])*t/3} ${p2[0]-(p3[0]-p1[0])*t/3} ${p2[1]-(p3[1]-p1[1])*t/3} ${p2[0]} ${p2[1]} `}return d+'Z'}
function glyphToVectorPath(bin,w,h,bounds,labels,compIds){const{x1,y1,x2,y2}=bounds;const gw=x2-x1+1,gh=y2-y1+1;if(gw<2||gh<2)return'';const local=new Uint8Array(gw*gh);for(let y=y1;y<=y2;y++)for(let x=x1;x<=x2;x++){const i=y*w+x;if(bin[i]&&(!compIds||!compIds.length||compIds.includes(labels[i])))local[(y-y1)*gw+(x-x1)]=1}let sx=-1,sy=-1;for(let y=0;y<gh&&sx<0;y++)for(let x=0;x<gw&&sx<0;x++)if(local[y*gw+x]){sx=x;sy=y}if(sx<0)return'';const oc=mooreTrace(local,gw,gh,sx,sy);if(oc.length<3)return'';let path=polyToBezier(simplify(oc,1.2));const bg=floodFillBg(local,gw,gh),holes=findHoles(local,gw,gh,bg);for(const hole of holes){const hp=new Uint8Array(gw*gh);for(const i of hole)hp[i]=1;let hx=-1,hy=-1;for(const i of hole){hy=(i/gw)|0;hx=i%gw;break}if(hx>=0){const hc=mooreTrace(hp,gw,gh,hx,hy),hs=simplify(hc,1.0);if(hs.length>2)path+=' '+polyToBezier(hs.reverse())}}return path}
function kMeansColors(px,k){if(px.length<k*3)return null;let cen=[];const step=Math.floor(px.length/k);for(let i=0;i<k;i++)cen.push(px[Math.min(i*step,px.length-1)].slice(0,3));const asgn=new Array(px.length);for(let iter=0;iter<12;iter++){for(let i=0;i<px.length;i++){let mn=Infinity,b=0;for(let c=0;c<k;c++){const dr=px[i][0]-cen[c][0],dg=px[i][1]-cen[c][1],db=px[i][2]-cen[c][2],d=dr*dr+dg*dg+db*db;if(d<mn){mn=d;b=c}}asgn[i]=b}const sums=Array.from({length:k},()=>[0,0,0,0]);for(let i=0;i<px.length;i++){const c=asgn[i];sums[c][0]+=px[i][0];sums[c][1]+=px[i][1];sums[c][2]+=px[i][2];sums[c][3]++}for(let c=0;c<k;c++)if(sums[c][3]>0)cen[c]=[sums[c][0]/sums[c][3],sums[c][1]/sums[c][3],sums[c][2]/sums[c][3]]}return{asgn,cen}}
// ---------- end verbatim ----------

// INGEST adaptation 1: paper-color background mask instead of the fork's
// otsu ink threshold (a letter scan is dark-on-paper; an illustration is a
// wash on paper). paper = median border color; fg = rgb distance from paper
// beyond `tol`, or alpha < 255.
function paperMask(d,w,h,tol){
  const border=[]
  for(let x=0;x<w;x+=4){border.push([x,0]);border.push([x,h-1])}
  for(let y=0;y<h;y+=4){border.push([0,y]);border.push([w-1,y])}
  const rs=[],gs=[],bs=[]
  for(const[bx,by]of border){const p=(by*w+bx)*4;if(d[p+3]>250){rs.push(d[p]);gs.push(d[p+1]);bs.push(d[p+2])}}
  rs.sort((a,b)=>a-b);gs.sort((a,b)=>a-b);bs.sort((a,b)=>a-b)
  const pr=rs[rs.length>>1],pg=gs[gs.length>>1],pb=bs[bs.length>>1]
  const bin=new Uint8Array(w*h)
  for(let i=0;i<w*h;i++){const p=i*4
    if(d[p+3]<200){bin[i]=1;continue}
    const dr=d[p]-pr,dg=d[p+1]-pg,db=d[p+2]-pb
    if(Math.sqrt(dr*dr+dg*dg+db*db)>tol)bin[i]=1}
  return{bin,paper:[pr,pg,pb]}
}

const [,,rawPath,wS,hS,kS,outSvg,outJson]=process.argv
const w=+wS,h=+hS,k=+kS
const buf=readFileSync(rawPath)
const d=new Uint8Array(buf.buffer,buf.byteOffset,buf.length)  // raw rgba
console.log(`input ${w}x${h}, ${k} clusters`)

const t0=Date.now()
const{bin,paper}=paperMask(d,w,h,26)
// small blur+open to kill paper grain speckle (INGEST: keep fork's blur fn)
const g=toGray(d,w,h)
const fgN=bin.reduce((a,b)=>a+b,0)
console.log(`foreground px: ${fgN} (${(100*fgN/(w*h)).toFixed(1)}%), paper rgb ${paper}`)

// k-means over foreground pixels (fork's clustering, verbatim math)
const px=[]
for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x;if(bin[i]){const p=i*4;px.push([d[p],d[p+1],d[p+2],x,y])}}
const{asgn,cen}=kMeansColors(px,k)
console.log(`k-means done in ${Date.now()-t0}ms`)
for(let c=0;c<k;c++){const n=asgn.filter(a=>a===c).length;console.log(`  zone ${c}: rgb(${cen[c].map(v=>v|0)}) ${n}px`)}

// INGEST adaptation 2: the fork traces one component per glyph; a whole
// illustration needs every component of every zone traced. same trace stack
// (moore -> simplify -> bezier + holes) via glyphToVectorPath, called once
// per connected component.
const zones=[]
for(let c=0;c<k;c++){
  const mask=new Uint8Array(w*h)
  for(let i=0;i<px.length;i++)if(asgn[i]===c)mask[px[i][4]*w+px[i][3]]=1
  const{labels,count}=labelComponents(mask,w,h)
  const B=getBounds(labels,w,h,count).slice(1)
  const comps=B.filter(b=>b.area>=12).sort((a,b)=>b.area-a.area)
  const paths=[]
  for(const b of comps){
    const idx=B.indexOf(b)+1
    const p=glyphToVectorPath(mask,w,h,{x1:b.x1,y1:b.y1,x2:b.x2,y2:b.y2},labels,[idx])
    if(p)paths.push({d:p,area:b.area})
  }
  const hex='#'+cen[c].map(v=>Math.round(v).toString(16).padStart(2,'0')).join('')
  zones.push({hex,paths,npx:comps.reduce((a,b)=>a+b.area,0),comps:comps.length})
  console.log(`  zone ${c} ${hex}: ${comps.length} components -> ${paths.length} paths`)
}

// svg out: zones painted big-to-small so lighter/matching regions layer under
const totalArea=zones.reduce((a,z)=>a+z.npx,0)
const order=[...zones].sort((a,b)=>b.npx-a.npx)
let svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">\n`
svg+=`<rect width="${w}" height="${h}" fill="rgb(${paper.join(',')})"/>\n`
for(const z of order)for(const p of z.paths)svg+=`<path d="${p.d}" fill="${z.hex}" fill-rule="nonzero"/>\n`
svg+='</svg>'
writeFileSync(outSvg,svg)

const stats={w,h,k,paper,fgPct:+(100*fgN/(w*h)).toFixed(1),
  zones:zones.map((z,i)=>({hex:z.hex,pctArea:+(100*z.npx/totalArea).toFixed(1),components:z.comps})),
  totalPaths:zones.reduce((a,z)=>a+z.paths.length,0),
  ms:Date.now()-t0,svgBytes:svg.length}
writeFileSync(outJson,JSON.stringify(stats,null,2))
console.log(`wrote ${outSvg} (${svg.length}b, ${stats.totalPaths} paths) in ${stats.ms}ms`)
