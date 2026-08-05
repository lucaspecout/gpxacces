import pytest
from app.gpx import Point, parse_gpx, resample

GPX=b'''<?xml version="1.0"?><gpx version="1.1"><trk><name>Démo</name><trkseg><trkpt lat="45" lon="5"><ele>100</ele></trkpt><trkpt lat="45.001" lon="5.001"><ele>110</ele></trkpt></trkseg></trk></gpx>'''
def test_valid_gpx():
    name,points=parse_gpx(GPX); assert name=="Démo" and len(points)==2
def test_rejects_entities():
    with pytest.raises(ValueError): parse_gpx(b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><gpx/>')
def test_rejects_invalid_coordinates():
    with pytest.raises(ValueError): parse_gpx(b'<gpx><trkpt lat="999" lon="5"/><trkpt lat="45" lon="5"/></gpx>')
def test_accepts_gpx_route_points():
    _, points=parse_gpx(b'<gpx><rte><rtept lat="45" lon="5"/><rtept lat="45.1" lon="5.1"/></rte></gpx>')
    assert len(points)==2
def test_resample_does_not_double_count_distance():
    points=[Point(45+i*.00001,5) for i in range(11)]
    assert len(resample(points,10))==2
