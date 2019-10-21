"""
Yuqi

This program will be implemented as a scheduler in master node
There is the workflow
1.watch kubernetes
2.when there is a pod in pending, read json reports from all worker nodes
3.using data from worker nodes to scheduler the pod
4.write the pod information into worker nodes json file

Potential problems:
1.When there are no jobs in any nodes, pick the one randomly
2.When there are some jobs inside but nothing report received from worker node, pick the one with less jobs
3.The master node now has no permission for pvc. We need to debug it.
4.We need to test whether it has a influence to read json while writing something inside.
"""
import time
import random
import json
import sys

from kubernetes import client, config, watch

config.load_kube_config()
v1 = client.CoreV1Api()

scheduler_name = "my-scheduler"


def nodes_available():
    ready_nodes = v1.list_node().items
    for n in v1.list_node().items:
        for status in n.status.conditions:
            if status.type == 'Ready':
                if status.status == "False":
                    ready_nodes.delete(n.metadata.name)
                    break
            else:
                if status.status == "True":
                    ready_nodes.delete(n.metadata.name)
                    break
    return ready_nodes




def scheduler(name, node, namespace='default'):
    target = client.V1ObjectReference(kind = 'Node', api_version = 'v1', name = node)
    meta = client.V1ObjectMeta(name = name)
    body = client.V1Binding(target = target, metadata = meta)
    try:
        client.CoreV1Api().create_namespaced_binding(namespace=namespace, body=body)
    except ValueError:
        # PRINT SOMETHING or PASS
        pass
def best_node():
    pass

def main():
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == scheduler_name:
            try:
                nodes = nodes_available()
                node = random.choice(nodes)
                f = open("/data/" + node + ".log", "a")
                f.write(str(event['object'].metadata.name) + ",")
                f.close()
                res = scheduler(event['object'].metadata.name, node)
                print event['object'].metadata.name+" has been locate to "+node
            except client.rest.ApiException as e:
                print json.loads(e.body)['message']


if __name__ == '__main__':
    main()