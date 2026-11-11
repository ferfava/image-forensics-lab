/* Casos reproducibles 768×512: originales + ediciones + máscaras, creados en el navegador.
 * No se optimizan con el SVM ni se consideran benchmark. Sin imágenes externas.
 */
(() => {
  "use strict";
  const W = 768, H = 512;
  const cases = {
    costa: {name:"costa_faro", region:{x:492,y:258,w:116,h:104}, tint:"#f9ae34"},
    escritorio: {name:"escritorio_nota", region:{x:454,y:214,w:154,h:123}, tint:"#fce969"},
    ciudad: {name:"ciudad_cartel", region:{x:441,y:149,w:160,h:110}, tint:"#ef4c83"},
  };
  const status = document.querySelector("#sample-status");
  const cards = document.querySelectorAll(".sample-card");
  function canvas() { const c=document.createElement("canvas"); c.width=W; c.height=H; return c; }
  function fill(ctx,x,y,w,h,color) {ctx.fillStyle=color;ctx.fillRect(x,y,w,h);}
  function polygon(ctx, points, color) {
    ctx.beginPath();ctx.moveTo(points[0][0],points[0][1]);
    points.slice(1).forEach(p=>ctx.lineTo(p[0],p[1]));
    ctx.closePath();ctx.fillStyle=color;ctx.fill();
  }
  function gradient(ctx,x,y,w,h,stops) {
    const g=ctx.createLinearGradient(x,y,x+w,y+h);
    stops.forEach(([t,color])=>g.addColorStop(t,color));
    return g;
  }
  function rng(seed) {let a=seed>>>0;return ()=>{a=(1664525*a+1013904223)>>>0;return a/4294967296;};}
  function drawCoast(ctx) {
    fill(ctx,0,0,W,H,gradient(ctx,0,0,0,350,[[0,"#25385a"],[0.48,"#dc8290"],[1,"#ffc883"]]));
    const random=rng(991);
    for(let i=0;i<95;i++){
      const x=random()*W,y=80+random()*170;
      ctx.fillStyle="rgba(255,237,215,"+(0.05+random()*0.14)+")";
      ctx.beginPath();ctx.ellipse(x,y,15+random()*85,2+random()*9,0,0,Math.PI*2);ctx.fill();
    }
    fill(ctx,0,322,W,190,gradient(ctx,0,322,0,190,[[0,"#477e92"],[1,"#102d52"]]));
    for(let i=0;i<160;i++){
      const x=random()*W,y=331+random()*181;
      fill(ctx,x,y,12+random()*70,1+random()*2,"rgba(255,211,159,0.20)");
    }
    polygon(ctx,[[0,380],[290,354],[460,420],[545,458],[390,512],[0,512]],"#48514c");
    for(let i=0;i<48;i++){const x=random()*470,y=386+random()*126;ctx.fillStyle=i%2?"#778075":"#383c3a";ctx.beginPath();ctx.ellipse(x,y,20+random()*50,10+random()*20,0,0,6.283);ctx.fill();}
    fill(ctx,170,264,142,117,"#f3eadb");fill(ctx,184,311,37,43,"#3d5058");
    polygon(ctx,[[150,264],[240,219],[336,265]],"#a6534a");
    polygon(ctx,[[242,110],[269,110],[296,265],[213,265]],"#eee1d6");
    fill(ctx,237,102,38,28,"#873e3b");fill(ctx,241,78,31,24,"#c65345");
    fill(ctx,238,143,38,7,"#272c37");fill(ctx,232,119,52,8,"#c85042");
    fill(ctx,204,262,14,19,"#38516b"); fill(ctx,276,270,16,20,"#38516b");
    fill(ctx,0,481,W,31,"#263e3d");
  }
  function drawDesk(ctx) {
    fill(ctx,0,0,W,H,gradient(ctx,0,0,0,400,[[0,"#263c5a"],[1,"#7594a4"]]));
    fill(ctx,0,0,255,345,"#aab5b7"); fill(ctx,18,21,214,278,"#cee4e8");
    fill(ctx,119,20,8,288,"#728993");fill(ctx,22,159,211,8,"#7895a2");
    fill(ctx,0,313,W,199,gradient(ctx,0,313,0,200,[[0,"#98724f"],[1,"#51382f"]]));
    for(let j=0;j<16;j++)fill(ctx,0,316+j*13,W,1,"rgba(30,23,25,.17)");
    // laptop keyboard
    polygon(ctx,[[184,345],[469,345],[535,430],[122,430]],"#303943");
    fill(ctx,187,158,281,187,"#252c3d");fill(ctx,198,169,258,163,"#86b0c7");
    fill(ctx,211,182,227,140,"#537c9c");fill(ctx,198,329,258,9,"#3c5363");
    for(let i=0;i<9;i++)for(let j=0;j<18;j++)fill(ctx,157+j*17-i,368+i*6,13,4,"#54616a");
    fill(ctx,585,340,83,17,"#d5d8d2");fill(ctx,603,276,47,69,"#efeee0");
    ctx.strokeStyle="#d5d2c6";ctx.lineWidth=9;ctx.beginPath();ctx.arc(650,310,34,-1.3,1.25);ctx.stroke();
    fill(ctx,49,365,51,86,"#8eaa8f");fill(ctx,67,308,16,61,"#688a7a");
    for(let i=0;i<4;i++){ctx.fillStyle="#4e8062";ctx.beginPath();ctx.ellipse(66+i*8,321+i*9,29,10,-0.6,0,6.283);ctx.fill();}
    fill(ctx,0,479,W,33,"#362a28");
  }
  function drawCity(ctx) {
    fill(ctx,0,0,W,H,gradient(ctx,0,0,0,500,[[0,"#12152c"],[0.65,"#39405c"],[1,"#776070"]]));
    const random=rng(786);
    for(let i=0;i<75;i++)fill(ctx,random()*W,random()*205,1.5,1.5,"#d5c4bb");
    fill(ctx,0,170,200,230,"#283247");fill(ctx,189,104,239,304,"#343b50");fill(ctx,428,79,232,320,"#4c4153");
    fill(ctx,655,148,113,259,"#283348");
    for(let x=214;x<407;x+=53)for(let y=133;y<350;y+=57)fill(ctx,x,y,26,34,(x+y)%3?"#ddad7a":"#6a8295");
    for(let x=454;x<640;x+=47)for(let y=110;y<333;y+=54)fill(ctx,x,y,25,29,(x+y)%4?"#e8aa78":"#63728c");
    for(let x=19;x<170;x+=51)for(let y=199;y<335;y+=50)fill(ctx,x,y,23,27,"#a49b8b");
    polygon(ctx,[[0,382],[W,370],[W,512],[0,512]],"#292c3d");
    polygon(ctx,[[282,399],[489,386],[768,512],[0,512]],"#4a4652");
    for(let i=0;i<10;i++)fill(ctx,335+i*49,435+i*5,21,2,"#a2a0a3");
    fill(ctx,45,375,94,37,"#99655f");fill(ctx,46,369,92,8,"#cf8f75");
    fill(ctx,668,360,15,95,"#333b42");fill(ctx,673,325,6,34,"#d1a977");
    ctx.fillStyle="#ffe1a1";ctx.beginPath();ctx.arc(676,322,12,0,6.283);ctx.fill();
  }
  function drawOriginal(kind) {
    const c=canvas(),ctx=c.getContext("2d");
    if(kind==="costa")drawCoast(ctx);
    else if(kind==="escritorio")drawDesk(ctx);
    else drawCity(ctx);
    return c;
  }
  function drawEdited(original,kind) {
    const c=canvas(),ctx=c.getContext("2d");
    ctx.drawImage(original,0,0);
    const {x,y,w,h,tint}=cases[kind].region;
    // Opaque rectangular insertion: the ground-truth annotation is independent
    // of the classifier and matches this exact edited region.
    fill(ctx,x,y,w,h,tint);
    ctx.strokeStyle="#20344d";ctx.lineWidth=6;ctx.strokeRect(x+4,y+4,w-8,h-8);
    if(kind==="costa"){
      ctx.strokeStyle="#153a50";ctx.lineWidth=9;ctx.beginPath();ctx.moveTo(x+58,y+19);ctx.lineTo(x+58,y+83);ctx.stroke();
      ctx.beginPath();ctx.arc(x+58,y+62,20,0,Math.PI);ctx.stroke();
      ctx.beginPath();ctx.moveTo(x+36,y+79);ctx.lineTo(x+80,y+79);ctx.stroke();
    } else if(kind==="escritorio"){
      fill(ctx,x+17,y+23,w-34,5,"#d87b5b");fill(ctx,x+17,y+49,w-48,5,"#a7a074");
      fill(ctx,x+17,y+75,w-42,5,"#a7a074");
      ctx.fillStyle="#ae7456";ctx.beginPath();ctx.arc(x+w-24,y+18,8,0,6.283);ctx.fill();
    } else {
      ctx.fillStyle="#fdf0f7";ctx.font="bold 37px system-ui";
      ctx.textAlign="center";ctx.fillText("OPEN",x+w/2,y+70);
      fill(ctx,x+22,y+83,w-44,5,"#fbc3d8");
    }
    return c;
  }
  function drawMask(kind) {
    const c=canvas(),ctx=c.getContext("2d"),{x,y,w,h}=cases[kind].region;
    fill(ctx,0,0,W,H,"#000000");fill(ctx,x,y,w,h,"#ffffff");
    return c;
  }
  const generated={};
  function source(kind) {
    if(!generated[kind]) {
      const original=drawOriginal(kind);
      generated[kind]={original,edited:drawEdited(original,kind),mask:drawMask(kind)};
    }
    return generated[kind];
  }
  function toPngFile(canvas,name) {
    return new Promise((resolve,reject)=>canvas.toBlob(blob=>
      blob ? resolve(new File([blob],name,{type:"image/png"})) : reject(new Error("No se pudo generar PNG.")),"image/png"));
  }
  function setFile(input,file) {
    const transfer=new DataTransfer();transfer.items.add(file);input.files=transfer.files;
    input.dispatchEvent(new Event("change",{bubbles:true}));
  }
  async function useExample(kind,action,button) {
    if(!cases[kind])throw new Error("Caso de prueba desconocido.");
    button.disabled=true;
    status.textContent="Preparando imágenes y máscara del caso "+cases[kind].name+"…";
    status.classList.remove("error");
    try {
      const images=source(kind);
      const name=cases[kind].name;
      if(action==="compare") {
        const [ref,edited,mask]=await Promise.all([
          toPngFile(images.original,name+"_original.png"),
          toPngFile(images.edited,name+"_editada.png"),
          toPngFile(images.mask,name+"_mascara.png")
        ]);
        setFile(document.querySelector("#compare-reference"),ref);
        setFile(document.querySelector("#compare-candidate"),edited);
        setFile(document.querySelector("#compare-ground-truth"),mask);
        document.querySelector("#compare-form").requestSubmit();
        document.querySelector("#comparador").scrollIntoView({behavior:"smooth",block:"start"});
        status.textContent="Caso cargado en el comparador con máscara independiente.";
      } else if(action==="analyze") {
        const file=await toPngFile(images.edited,name+"_editada.png");
        setFile(document.querySelector("#photo"),file);
        document.querySelector("#analyze-form").requestSubmit();
        status.textContent="Imagen editada cargada para analizar bordes, filtros y ELA.";
      } else if(action==="ml") {
        const file=await toPngFile(images.edited,name+"_editada.png");
        setFile(document.querySelector("#ml-photo"),file);
        document.querySelector("#machine-learning").scrollIntoView({behavior:"smooth",block:"start"});
        if(!document.querySelector("#ml-button").disabled) {
          document.querySelector("#ml-form").requestSubmit();
          status.textContent="Predicción SVM iniciada. No equivale a validación del modelo.";
        } else {
          status.textContent="Ejemplo listo en ML; el servidor actual no tiene modelo instalado.";
        }
      }
    } catch(error) {
      status.classList.add("error");
      status.textContent="No se pudo preparar el ejemplo: "+error.message;
    } finally {button.disabled=false;}
  }
  for(const card of cards) {
    const kind=card.dataset.sample;
    const thumbnail=card.querySelector(".sample-preview");
    if(cases[kind] && thumbnail) {
      thumbnail.getContext("2d").drawImage(source(kind).edited,0,0,thumbnail.width,thumbnail.height);
      card.querySelectorAll("[data-sample-action]").forEach(button=>
        button.addEventListener("click",()=>useExample(kind,button.dataset.sampleAction,button)));
    }
  }
})();
