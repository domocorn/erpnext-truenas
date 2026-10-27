"""Read-only queue gate: do not migrate across pending or unresolved RQ work."""


def check_queues(queues, registry_types):
    for queue in queues:
        if queue.count:
            raise RuntimeError('Queued work must be drained before migration')
        for registry_type in registry_types:
            registry = registry_type(name=queue.name, connection=queue.connection)
            # Never let an inspection clean up stale started jobs automatically.
            if registry.get_job_ids(cleanup=False):
                raise RuntimeError('Unresolved RQ work must be reviewed before migration')


def require_empty():
    from redis import Redis
    from rq import Queue
    from rq.registry import StartedJobRegistry, DeferredJobRegistry, ScheduledJobRegistry, FailedJobRegistry
    connection = Redis.from_url('redis://redis-queue:6379', socket_connect_timeout=5, socket_timeout=5)
    connection.ping()
    check_queues(Queue.all(connection=connection),
        (StartedJobRegistry, DeferredJobRegistry, ScheduledJobRegistry, FailedJobRegistry))
