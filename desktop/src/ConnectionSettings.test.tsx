import {fireEvent,render,screen} from '@testing-library/react';
import {expect,it,vi} from 'vitest';
import {ConnectionSettings} from './ConnectionSettings';
import {initialView} from './bridge';

it('sends only the endpoint before displaying public registration and an exact invitation',()=>{
  const run=vi.fn().mockResolvedValue(true);
  const {rerender}=render(<ConnectionSettings view={initialView} busy={false} run={run}/>);
  fireEvent.change(screen.getByLabelText('Core address'),{target:{value:'https://core.example'}});
  fireEvent.click(screen.getByText('Prepare this device'));
  expect(run).toHaveBeenCalledWith({kind:'connection_prepare',url:'https://core.example'});
  rerender(<ConnectionSettings view={{...initialView,connection:{endpoint:'https://core.example',installation_id:'installation',node_id:null,public_key:'public transport',owner_public_key:'public owner',status:'awaiting_enrollment'}}} busy={false} run={run}/>);
  fireEvent.change(screen.getByLabelText('Approved device invitation'),{target:{value:'{"challenge_id":"bound"}'}});
  fireEvent.click(screen.getByText('Review and connect'));
  expect(run).toHaveBeenCalledWith({kind:'connection_enroll',invitation:'{"challenge_id":"bound"}'});
  fireEvent.click(screen.getByText('Disconnect and forget this device'));
  expect(run).toHaveBeenCalledWith({kind:'connection_logout'});
});
