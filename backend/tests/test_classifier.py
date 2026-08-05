from app.classifier import classify
from app.gpx import Point
from app.models import WayInfo
from app.main import merge_by_class
def test_paved_road_is_green():
    s=classify(0,Point(45,5,100),Point(45.0001,5,100),WayInfo(distance_m=2,tags={"highway":"residential","surface":"asphalt"}))
    assert s.classification=="green" and s.score>=70
def test_private_path_is_red():
    s=classify(0,Point(45,5),Point(45.0001,5),WayInfo(distance_m=2,tags={"highway":"path","access":"private"}))
    assert s.classification=="red"
def test_missing_data_is_gray(): assert classify(0,Point(45,5),Point(45.001,5)).classification=="gray"
def test_distant_way_is_insufficient():
    s=classify(0,Point(45,5),Point(45.001,5),WayInfo(distance_m=80,tags={"highway":"primary"}))
    assert s.classification=="gray"
def test_suv_profile_improves_score():
    way=WayInfo(distance_m=2,tags={"highway":"track","surface":"ground"})
    assert classify(0,Point(45,5),Point(45.001,5),way,"suv").score > classify(0,Point(45,5),Point(45.001,5),way).score
def test_consecutive_equal_classes_are_merged():
    way=WayInfo(distance_m=2,tags={"highway":"residential","surface":"asphalt"})
    first=classify(0,Point(45,5),Point(45.0001,5),way)
    second=classify(1,Point(45.0001,5),Point(45.0002,5),way)
    merged=merge_by_class([first,second])
    assert len(merged)==1 and len(merged[0].coordinates)==3
