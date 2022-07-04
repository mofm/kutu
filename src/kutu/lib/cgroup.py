import os
import logging

logger = logging.getLogger(__name__)

BASE_CGROUPS = "/sys/fs/cgroup/"
# we support only cpu ve memory cgroup for now
HIERARCHIES = [
    'cpu',
    'memory',
]
MEMORY_DEFAULT = -1
CPU_DEFAULT = 1024


class CgroupsException(Exception):
    pass


def get_kutu_cgroup():
    kutu_cgroups = {}
    for cgroup in HIERARCHIES:
        kutu_cgroup = os.path.join(BASE_CGROUPS, cgroup, "kutu")
        kutu_cgroups[cgroup] = kutu_cgroup

    return kutu_cgroups


def create_kutu_cgroups(group='kutu'):
    # Get hierarchies and create cgroups sub-directories
    try:
        hierarchies = os.listdir(BASE_CGROUPS)
    except OSError as exc:
        if exc.errno == 2:
            raise CgroupsException(
                "cgroups filesystem is not mounted on {}".format(BASE_CGROUPS))
        else:
            raise OSError(exc)
    for hierarchy in hierarchies:
        kutu_cgroup = os.path.join(BASE_CGROUPS, hierarchy, group)
        if not os.path.exists(kutu_cgroup):
            try:
                os.mkdir(kutu_cgroup)
            except OSError as exc:
                if exc.errno == 13:
                    raise CgroupsException(
                        "Permission denied, you don't have root privileges")
                elif exc.errno == 17:
                    pass
                else:
                    raise OSError(exc)


class Cgroup(object):

    def __init__(self, name, hierarchies='all', group='kutu'):
        self.name = name
        # Get Group
        self.group = group
        # Get hierarchies
        if hierarchies == 'all':
            hierachies = HIERARCHIES
        self.hierarchies = [h for h in hierachies if h in HIERARCHIES]
        # Get user cgroups
        self.kutu_cgroups = {}
        system_hierarchies = os.listdir(BASE_CGROUPS)
        for hierarchy in self.hierarchies:
            if hierarchy not in system_hierarchies:
                raise CgroupsException(
                    "Hierarchy {} is not mounted".format(hierarchy))
            kutu_cgroup = os.path.join(BASE_CGROUPS, hierarchy, self.group)
            self.kutu_cgroups[hierarchy] = kutu_cgroup
        create_kutu_cgroups(self.group)
        # Create name cgroups
        self.cgroups = {}
        for hierarchy, kutu_cgroup in self.kutu_cgroups.items():
            cgroup = os.path.join(kutu_cgroup, self.name)
            if not os.path.exists(cgroup):
                os.mkdir(cgroup)
            self.cgroups[hierarchy] = cgroup

    def _get_cgroup_file(self, hierarchy, file_name):
        return os.path.join(self.cgroups[hierarchy], file_name)

    def _get_kutu_file(self, hierarchy, file_name):
        return os.path.join(self.kutu_cgroups[hierarchy], file_name)

    def delete(self):
        for hierarchy, cgroup in self.cgroups.items():
            # Put all pids of name cgroup in user cgroup
            tasks_file = self._get_cgroup_file(hierarchy, 'tasks')
            with open(tasks_file, 'r+') as f:
                tasks = f.read().split('\n')
            kutu_tasks_file = self._get_kutu_file(hierarchy, 'tasks')
            with open(kutu_tasks_file, 'a+') as f:
                f.write('\n'.join(tasks))
            os.rmdir(cgroup)

    # PIDS
    def add(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            raise CgroupsException("Pid {} does not exists".format(pid))
        for hierarchy, cgroup in self.cgroups.items():
            tasks_file = self._get_cgroup_file(hierarchy, 'tasks')
            with open(tasks_file, 'r+') as f:
                cgroups_pids = f.read().split('\n')
            if not str(pid) in cgroups_pids:
                with open(tasks_file, 'a+') as f:
                    f.write("{}\n".format(pid))

    def remove(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            raise CgroupsException("Pid {} does not exists".format(pid))
        for hierarchy, cgroup in self.cgroups.items():
            tasks_file = self._get_cgroup_file(hierarchy, 'tasks')
            with open(tasks_file, 'r+') as f:
                pids = f.read().split('\n')
                if str(pid) in pids:
                    kutu_tasks_file = self._get_kutu_file(hierarchy, 'tasks')
                    with open(kutu_tasks_file, 'a+') as file:
                        file.write("{}\n".format(pid))

    @property
    def pids(self):
        hierarchy = self.hierarchies[0]
        tasks_file = self._get_cgroup_file(hierarchy, 'tasks')
        with open(tasks_file, 'r+') as f:
            pids = f.read().split('\n')[:-1]
        pids = [int(pid) for pid in pids]
        return pids

    # CPU
    def _format_cpu_value(self, limit=None):
        if limit is None:
            value = CPU_DEFAULT
        else:
            try:
                limit = float(limit)
            except ValueError:
                raise CgroupsException('Limit must be convertible to a float')
            else:
                if limit <= float(0) or limit > float(100):
                    raise CgroupsException('Limit must be between 0 and 100')
                else:
                    limit = limit / 100
                    value = int(round(CPU_DEFAULT * limit))
        return value

    def set_cpu_limit(self, limit=None):
        if 'cpu' in self.cgroups:
            value = self._format_cpu_value(limit)
            cpu_shares_file = self._get_cgroup_file('cpu', 'cpu.shares')
            with open(cpu_shares_file, 'w+') as f:
                f.write("{}\n".format(value))
        else:
            raise CgroupsException(
                'CPU hierarchy not available in this cgroup')

    @property
    def cpu_limit(self):
        if 'cpu' in self.cgroups:
            cpu_shares_file = self._get_cgroup_file('cpu', 'cpu.shares')
            with open(cpu_shares_file, 'r+') as f:
                value = int(f.read().split('\n')[0])
                value = int(round((value / CPU_DEFAULT) * 100))
                return value
        else:
            return None

    # MEMORY
    def _format_memory_value(self, unit, limit=None):
        units = ['B', 'KiB', 'MiB', 'GiB']
        if unit not in units:
            raise CgroupsException("Unit must be in {}".format(units))
        if limit is None:
            value = MEMORY_DEFAULT
        else:
            try:
                limit = int(limit)
            except ValueError:
                raise CgroupsException('Limit must be convertible to an int')
            else:
                value = limit * 2**(units.index(unit)*10)
        return value

    def set_memory_limit(self, limit=None, unit='megabytes'):
        if 'memory' in self.cgroups:
            value = self._format_memory_value(unit, limit)
            memory_limit_file = self._get_cgroup_file(
                'memory', 'memory.limit_in_bytes')
            with open(memory_limit_file, 'w+') as f:
                f.write("{}\n".format(value))
        else:
            raise CgroupsException(
                'MEMORY hierarchy not available in this cgroup')

    @property
    def memory_limit(self):
        if 'memory' in self.cgroups:
            memory_limit_file = self._get_cgroup_file(
                'memory', 'memory.limit_in_bytes')
            with open(memory_limit_file, 'r+') as f:
                value = f.read().split('\n')[0]
                value = int(int(value) / 1024 / 1024)
                return value
        else:
            return None
