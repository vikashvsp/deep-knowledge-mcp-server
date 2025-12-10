import subprocess
import sys
import os
import json
import time

def run_smoke_test():
    # Check for APIFY_TOKEN
    if "APIFY_TOKEN" not in os.environ:
        print("WARNING: APIFY_TOKEN is not set. Tool calls will fail, but we can check the server startup and tool listing.")
    
    # Path to the server module
    server_cmd = [sys.executable, "-m", "src.main"]
    
    print(f"Starting server with command: {' '.join(server_cmd)}")
    
    process = subprocess.Popen(
        server_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0 # Unbuffered
    )
    
    try:
        # 1. Send Initialize Request (Simulating an MCP Client)
        # JSON-RPC 2.0
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        }
        
        print("Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response (might be multiple lines if logging happens)
        # We need to read line by line until we get a valid JSON with id 1
        response_found = False
        while not response_found:
            line = process.stdout.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
                
            print(f"Received: {line}")
            try:
                msg = json.loads(line)
                if msg.get("id") == 1:
                    print("Initialize successful!")
                    print(json.dumps(msg, indent=2))
                    response_found = True
            except json.JSONDecodeError:
                print(f"Log: {line}")

        # 2. List Tools
        list_tools_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("\nSending tools/list request...")
        process.stdin.write(json.dumps(list_tools_req) + "\n")
        process.stdin.flush()
        
        response_found = False
        while not response_found:
            line = process.stdout.readline()
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
            
            try:
                msg = json.loads(line)
                if msg.get("id") == 2:
                    print("Tools list received!")
                    tools = msg.get("result", {}).get("tools", [])
                    print(f"Found {len(tools)} tools:")
                    for t in tools:
                        print(f"- {t['name']}: {t['description']}")
                    response_found = True
            except json.JSONDecodeError:
                pass

        # 3. Test Tool Call
        if os.environ.get("APIFY_TOKEN"):
            print("\nAPIFY_TOKEN found. Testing 'search_technical_docs'...")
            tool_call_req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search_technical_docs",
                    "arguments": {
                        "query": "MCP server python",
                        "max_results": 1
                    }
                }
            }
            process.stdin.write(json.dumps(tool_call_req) + "\n")
            process.stdin.flush()
            
            response_found = False
            start_time = time.time()
            while not response_found and (time.time() - start_time < 30): # 30s timeout
                line = process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                
                try:
                    msg = json.loads(line)
                    if msg.get("id") == 3:
                        print("Tool call result received!")
                        print(json.dumps(msg, indent=2))
                        response_found = True
                    elif "method" in msg: 
                         # Ignore notifications/logging
                         pass
                except json.JSONDecodeError:
                    print(f"Log: {line}")
        else:
             print("\nSkipping tool call test (APIFY_TOKEN not set)")

    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        print("\nClosing server...")
        try:
            process.terminate()
            stdout, stderr = process.communicate(timeout=2)
            if stderr:
                print(f"Server Stderr:\n{stderr}")
        except:
            pass

if __name__ == "__main__":
    run_smoke_test()
