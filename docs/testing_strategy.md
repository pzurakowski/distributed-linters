# Testing strategy

## Machine management

### Machine creation
- Call `/create/{lang}` with chosen language and wait for response.
- **Check**: Response should be OK.
- **Check**: New containers should be created with the chosen language. (Check output of `docker ps` on the host machine).
- Call `/status` and wait for response.
- **Check**: Newly created machine is included in response.

### Machine removal
- Add 1 machine (see Machine creation) with the chosen language.
- Call `/status` to get the newly created machine’s IP and port.
- Call `/remove/{IP:port}` and wait for response.
- **Check**: Response should be OK.
- **Check**: The container should be removed. (Check output of `docker ps` on the host machine).
- Call `/status` and wait for response.
- **Check**: The container should NOT be included in the response.

### MM determines created machine version
- Call `/create/{lang}` with chosen language 10 times, wait for response each time.
- Call `/init-update/{version, lang}` to start updating to a new version.
- Call `/create/{lang}`, wait for response.
- **Check**: Response should be OK.
- Call `/status`.
- **Check**: There should be 10 machines on the old version, 1 machine on the new version.

### MM keeps machine ratio during the update
- Call `/create/{lang}` with chosen language 2 times, wait for response each time.
- Call `/init-update/{version, lang}` to start updating to a new version.
- Call `/status`.
- **Check**:
    - For the current update ratio in [1%, 5%, 10%, 50%] there should be 1 machine on the old version, 1 on the new version.
    - For the current update ratio 100%, both machines should be on the new version.
- Repeat steps 3-4 until we hit update ratio 100% (check MM config to keep track of ratios).

### MM keeps the machine update ratio during the update for a more complicated number of machines
- Create 11 machines calling by `/create` repeatedly, check if every return is OK.
- Call `/init-update/{version, lang}` to start updating to a new version.
- Call `/status`.
- **Check**: number of machines using given version should be determined by current update ratio:
    - update ratio in [1%, 5%] - 1 machine updated (ceil of 0.11 and 0.55)
    - update ratio is 10% - 2 machines updated (ceil of 1.1)
    - update ratio is 50% - 6 machines updated (ceil of 5.5)
    - update ratio is 100% - 11 machines updated
- Repeat steps 3-4 until we hit update ratio 100% (check MM config to keep track of ratios).

### add/remove roundtrip 
- final status same as initial

### update/rollback roundtrip: 
- final status same as initial


## Load balancer:
- test behavior when there are no linters available
- test behavior when there is no running update, just if all linters of certain version get equal amount of request
- test behavior when there is a running update, if all linters get load adequate to their weight, divided by the number of linters.
- Since for every `/ratio` request algorithm state is restarted, and added linter lands at the end of the thread-safe queue that’s sufficient number of tests, all complicated cases are handled by the machine manager, so they are tested there.

## Machine management + load balancer

### “MM determines the created machine version” but with checking traffic ratios. 
- Use standard update steps i.e. [1, 5, 10, 50, 100]
- Call `/create/{lang}` with chosen language 9 times, wait for response each time.
- Call `/init-update/{version, lang}` to start updating to a new version. (This will already update one of the machines to the new version).
- Call `/create/{lang}`
- **Check**:
    - 9 machines are on the old version, 1 on the new version
    - Send 100 requests to load balancer.
- Call `/status`.
- **Check**:
    - machines on the old version should receive 11 each (because 100 - 1 = 99, 99 / 9 = 11)
    - machines on the new version should receive 1 request.

### “MM keeps the machine update ratio during the update” but with checking traffic ratios.
- Call `/create/{lang}` with chosen language 2 times, wait for response each time.
- Call `/init-update/{version, lang}` to start updating to a new version.
- Call `/status`.
- Call `/lint/{lang}` on load balancer 100 times.
- **Check**:
    - For the current update ratio in [1%, 5%, 10%, 50%] there should be 1 machine on the old version, 1 on the new version.
    - For the current update ratio 100%, both machines should be on the new version.
- **Check**: Traffic ratio should be split exactly like current update step. 


## Fault injection

### Check if a machine failing a health check is removed from LB. 
- For this test use the linter that fails after receiving ‘request of death’, so we can simulate a machine failing.
- Call `/create/{lang}` with chosen language 2 times, wait for response each time.
- Send ‘request of death’ to Load Balancer’s lint endpoint. One of the machines should receive it and become unhealthy after that.
- Wait 2 * health_check_timeout, so that the Machine Manager will notice the unhealthy linter.
- Call `/status`.
- **Check**: One of the machines is marked as unhealthy. Note the ip of that machine.
- Send 100 requests to Load Balancer’s `/lint` endpoint.
- Call `/status`.
- **Check**: All requests were served by the machine that wasn’t marked unhealthy.


## Unit tests 
- Unit tests are not described in detail in this document, they will be created during the implementation.
- LB Unit tests
    - Unit tests for basic fundamental operations of manager of internal state of LoadBalancer: Uris and VersionRoundRobin
- MM Unit tests 
    - Unit tests for a sub-module keeping track of current version and update progress for each language.
    - Unit tests for sub-module performing the health check.
    - Unit tests for sub-module performing the actual creation/deletion of linter containers.
