# Design document

## Linter (Internal API)
- 2 programs (dockerized) - each for different programming languages: Python, Java. The list of languages is not hardcoded and can be extended if needed.
- Implementation: fastapi - for ease of development
- 4 versions per each linter - one “perfect”, one slightly different (with another linting rule), one which crashes often (for testing), one which processes the requests slower.
- Endpoints:
    - Linting:
        - `/lint` -> Linting code
    - Health check:
        - `/health` -> Basic information about linter and it’s state 

## Load Balancer (Public API)
- One machine
- Has a set of handled IPs
- Has two load balancing sets - one for linters, one for linter version weights
- Endpoints:
    - `/lint/language`  -> Forward request to linter 


## Load Balancer (Internal API)
- All the requests to the Internal API need an additional ‘secretKey’ parameter - this is to only allow admin to perform these requests. In the context of the whole project, the end user won’t use those endpoints directly - it will be handled by Machine Manager.
- Endpoints:
    - `/health` -> Check if load balancer is healthy
    - `/add ` -> Add linter to the balancing set
    - `/remove` -> Remove linter from the balancing set
    - `/ratio` -> Update weights for load balancing algorithm 
- Since we want to guarantee some traffic ratio, our load balancing algorithm needs to be weighted, `/ratio` endpoint takes required weights. The endpoint accepts an arbitrary number of versions and traffic percentages for them - the only requirement is that the ratios must sum up to a picked value (in default configuration: 100).
- We implement one load balancing algorithm (design allows for different one, but we don’t provide it)

## Machine Manager (Public API)
- We define a machine as a docker container. Machines created by Machine Manager are identified by the ip+port on which they expose the linting service. Machine Manager keeps additional information about each linter such as their health.
- Endpoints:
    - `/create` -> create linter for given language and return OK with ip+port when the machine is available (or ERROR if creating the machine didn’t succeed), the version is determined by the machine manager automatically based on the current phase of the update for each language.
    - `/remove` - remove machine with given IP:port, return OK when machine is removed.
    - `/init-update` Inits update to the specified version for specified language. After calling this endpoint, Machine Manager will change the version of some linters, to keep the first machine/traffic ratio specified in config.
    - `/update` - go to next machine/traffic ratio from config
    - `/rollback` - go to previous machine/traffic ratio from config
    - `/status` - information about running linters
- Health Check
    - MM sends a request to /health to every machine in regular, configurable intervals.
    - If a machine fails to respond:
        - it is marked as unhealthy (“is_healthy”==”false” for that machine in /status request).
        - MM requests LB to have it removed.
        - unhealthy machines are assumed to stay unhealthy (so they cannot get back up again - we don’t check for that).

## Update
- Gradual update ratios are stored in a config file (so we have predefined steps and admin cannot request specific ratio i.e. 69.96%) - initial is 1,5,10,50,100
- Load balancer will take care of the exact traffic ratio, but we also want to keep the machine ratio as good as we can (ceil of ratio value)
- Some machines are being killed and then replaced (but not necessarily with the same ip+port as before) with the new version.

## Communication with Load Balancer
- After each call to `/init-update`, `/update` or `/rollback` endpoints, Machine Manager will automatically inform the Load Balancer about recent changes, so that requests will be routed to correct machines and correct traffic ratio will be kept. 

## Docker Images Store
- Container images are stored in GHCR.

## Machine Manager config file
- Part of Machine Manager service. Config is stored locally in a text file on the Machine Manager host. It includes settings for:
    - Start timeout
    - Update steps (machine/traffic ratio during each phase of new version rollout)
    - Remove timeout
    - Health Check frequency
    - The file is updated manually, we do not provide functionality for changing it from the outside.

## Out of scope, potential improvements
- supporting other definitions of “machine”, i.e. VMs, physical servers
- different load balancing algorithms
- more than two versions of linter at the same time
- API for changing configuration variables for Machine Manager
- API for managing container images for Machine Manager
- logging

