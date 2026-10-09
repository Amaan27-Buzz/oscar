import React from 'react';
import {createRoot} from 'react-dom/client';
import {Lab} from './Lab';
import {EngineProof} from './EngineProof';
import './style.css';

createRoot(document.getElementById('root')!).render(<React.StrictMode>{new URLSearchParams(location.search).has('engine')?<EngineProof/>:<Lab/>}</React.StrictMode>);
