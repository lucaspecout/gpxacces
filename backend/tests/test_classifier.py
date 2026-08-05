from app.classifier import classify
from app.gpx import Point
from app.models import WayInfo
def test_paved_road_is_green():
    s=classify(0,Point(45,5,100),Point(45.0001,5,100),WayInfo(distance_m=2,tags={"highway":"residential","surface":"asphalt"}))
    assert s.classification=="green" and s.score>=70
def test_private_path_is_red():
    s=classify(0,Point(45,5),Point(45.0001,5),WayInfo(distance_m=2,tags={"highway":"path","access":"private"}))
    assert s.classification=="red"
def test_missing_data_is_gray(): assert classify(0,Point(45,5),Point(45.001,5)).classification=="gray"

