import {useState} from 'react';
import type {ReactNode} from 'react';
import {Popover,RadioGroup,Theme} from '@radix-ui/themes';
import * as Collapsible from '@radix-ui/react-collapsible';
import '@radix-ui/themes/styles.css';
export function Choice({label,value,onChange,options,placeholder='Choose an option',disabled=false}:{label:string;value:string;onChange:(value:string)=>void;options:{value:string;label:string}[];placeholder?:string;disabled?:boolean}) {
 const [open,setOpen]=useState(false);
 return <Theme asChild><span className="oscar-choice"><Popover.Root open={open} onOpenChange={setOpen} modal={false}><Popover.Trigger><button className="oscar-choice-trigger" aria-label={label} data-value={value} disabled={disabled} onKeyDown={e=>{if(e.key==='ArrowDown'){e.preventDefault();setOpen(true);}}}>{options.find(item=>item.value===value)?.label??placeholder}<span className="choice-sign" aria-hidden="true">{open?'−':'+'}</span></button></Popover.Trigger><Popover.Content className="oscar-choice-popup" size="1" sideOffset={6} align="start"><RadioGroup.Root aria-label={`${label} choices`} value={value} onValueChange={onChange}>{options.filter(item=>item.value!=='').map(item=><RadioGroup.Item key={item.value} value={item.value} onClick={()=>setOpen(false)}>{item.label}</RadioGroup.Item>)}</RadioGroup.Root></Popover.Content></Popover.Root></span></Theme>;
}
export function Disclosure({title,children,className='',defaultOpen=false}:{title:ReactNode;children:ReactNode;className?:string;defaultOpen?:boolean}) {
 return <Collapsible.Root className={`oscar-disclosure ${className}`} defaultOpen={defaultOpen}><Collapsible.Trigger className="oscar-disclosure-trigger"><span>{title}</span><span className="disclosure-sign" aria-hidden="true"/></Collapsible.Trigger><Collapsible.Content className="oscar-disclosure-content">{children}</Collapsible.Content></Collapsible.Root>;
}
