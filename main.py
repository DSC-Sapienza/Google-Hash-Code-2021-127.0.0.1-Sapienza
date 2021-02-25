from dataclasses import dataclass
from typing import *



@dataclass
class Inters:
  start_intersect: int  
  end_intersect: int
  required_time: int

@dataclass
class PlannedPath:
  n_paths: int
  list_paths: List[str]

@dataclass
class GreenLight:
    # street identifier for which the green light sometimes pops up
    street_id: str

    # how long should the green light stay on for
    duration: int

@dataclass
class Schedule:
    # intersection affected by this schedule
    intersection_id: int

    # green light durations associated with particular streets
    street_greenlights: List[GreenLight]

@dataclass
class Output:
    schedules: List[Schedule]

    def to_file(self, filename: str):
        with open("output/"+ filename, "w") as f_out:
            n_scheds = len(self.schedules)
            f_out.write(f"{n_scheds}\n")

            for schedule in self.schedules:
                f_out.write(f"{schedule.intersection_id}\n")
                f_out.write(f"{len(schedule.street_greenlights)}\n")
                for street_greenlight in schedule.street_greenlights:
                    f_out.write(f"{street_greenlight.street_id} ")
                    f_out.write(f"{street_greenlight.duration}\n")
            
            f_out.flush()


def from_file(filename: str) -> Tuple[List, List, List]:
    with open(filename, 'r') as file_writer:
        file_input: List[str] = [line.strip().split() for line in file_writer.readlines()]
        header: List[int] = [int(item) for item in file_input[0]]
        file_input = file_input[1:]
        sim_duration, n_intersection, n_streets, n_paths, score = header
        streets_list = file_input[:n_streets]
        assert len(streets_list) == n_streets
        paths_list = file_input[n_streets:]
        assert len(paths_list) == n_paths

        for i in range(len(paths_list)):
            paths_list[i][0] = int(paths_list[i][0])

        for i in range(len(streets_list)):
            street = streets_list[i]
            street[0] = int(street[0])
            street[1] = int(street[1])
            street[3] = int(street[3])

    return header, streets_list, paths_list
    
    


class SimulationProblem():
    def __init__(self, filename: str):
        self.filename = filename
        self.header, streets_list, paths_list = from_file(filename)
        self.sim_duration, self.n_intersection, self.n_streets, self.n_paths, self.score = self.header
        self.planned_path: List[PlannedPath] = SimulationProblem.planned_paths_factory(paths_list)
        self.intersect: Dict[str, Inters] = SimulationProblem.intersect_factory(streets_list) 
        self.count_in_degree()
        self.schedule_list = self.always_green_light()

    @staticmethod
    def intersect_factory(streets_list: list) -> Dict[str, Inters]:
        result: Dict[str:Inters] = {street[2]: Inters(start_intersect=street[0], end_intersect=street[1], required_time=street[3]) for street in streets_list}
        return result
    @staticmethod
    def planned_paths_factory(planned_paths_list: list) -> PlannedPath:
        result: List[PlannedPath] = [PlannedPath(n_paths=path[0], list_paths=path[1:]) for path in planned_paths_list]
        return result

    def count_in_degree(self):
        self.city_to_in_degree: dict = {}
        for street in self.intersect.keys():
            city = self.intersect[street].end_intersect
            if city not in self.city_to_in_degree:
                self.city_to_in_degree[city] = [1, [street]]
            else:
                self.city_to_in_degree[city][0] += 1
                self.city_to_in_degree[city][1].append(street)

    def always_green_light(self):
        # pre calculate all street with 1 in degree, so always green
        result = []
        for city in self.city_to_in_degree.keys():
            in_degree = self.city_to_in_degree[city][0]
            street_id = self.city_to_in_degree[city][1][0]
            if in_degree == 1:
                gl_list = [GreenLight(street_id=str(street_id), duration=self.sim_duration)]
                s = Schedule(intersection_id=int(city), street_greenlights=gl_list)
                result.append(s)
        return result

    def count_cars(self):
        cars = dict()
        # iterate over cars' paths
        for p in self.planned_path:
            # iterate over streets in a path
            for street in p.list_paths:
                # increment cars passing along that street
                if street in cars:
                    cars[street] += 1
                else:
                    cars[street] = 1
        return cars

def round_robin_naive(problem: SimulationProblem) -> Output:
    schedules = problem.always_green_light()
    for city, (in_degree, list_of_street) in problem.city_to_in_degree.items():
        if in_degree == 1:
           continue
        sg = [GreenLight(street_id=s, duration=1) for s in list_of_street]
        schedules.append(Schedule(intersection_id=city, street_greenlights=sg))

    ret = Output(schedules)
    return ret

def round_robin_weighted(problem: SimulationProblem) -> Output:
    cars_count = problem.count_cars()
    total_cars = dict()
    schedules = problem.always_green_light()
    for city, (in_degree, list_of_street) in problem.city_to_in_degree.items():
        if in_degree == 1:
           continue

        for street in list_of_street:
            if city in total_cars:
                total_cars[city] += cars_count.get(street, 0)
            else:
                total_cars[city] = cars_count.get(street, 0)

        sg = [GreenLight(street_id=s, duration=min(problem.sim_duration, cars_count.get(s,0))) for s in list_of_street]
        sg = list(filter(lambda x: x.duration > 0, sg))
        if len(sg) > 0:
            schedules.append(Schedule(intersection_id=city, street_greenlights=sg))

    ret = Output(schedules)
    return ret

if __name__ == '__main__':
    for f in ['a', 'b', 'c', 'd', 'e', 'f']:
        print("running file ", f)
        inp = SimulationProblem("input/"+ f+".txt")
        round_robin_naive(inp).to_file(inp.filename.replace("input/", "").replace(".txt", "") + '_out.txt')
    exit(0)

