from tests import FlexGetBase
from flexget.utils import qualities as quals


class TestQualityParser(object):

    def test_quals(self):
        items = [('Test.File.1080p.web-dl', '1080p web-dl'),
                ('Test.File.web-dl.1080p', '1080p web-dl'),
                ('Test.File.720p.webdl', '720p web-dl'),
                ('Test.File.1280x720_web dl', '720p web-dl'),
                ('Test.File.720p.h264.web.dl', '720p web-dl'),
                ('Test.File.web-dl', 'web-dl'),
                ('Test.File.720p', '720p'),
                ('Test.File.1920x1080', '1080p')]
        for item in items:
            quality = quals.parse_quality(item[0]).name
            assert quality == item[1], 'quality should be %s not %s' % (item[1], quality)


class TestFilterQuality(FlexGetBase):

    __yaml__ = """
        presets:
          global:
            mock:
              - {title: 'Smoke.1280x720'}
              - {title: 'Smoke.HDTV'}
              - {title: 'Smoke.cam'}
              - {title: 'Smoke.HR'}
            accept_all: yes
        feeds:
          qual:
            quality:
              - hdtv
              - 720p
          min:
            quality:
              min: HR
          max:
            quality:
              max: cam
          min_max:
            quality:
              min: HR
              max: 720i
    """

    def test_quality(self):
        self.execute_feed('qual')
        entry = self.feed.find_entry('rejected', title='Smoke.cam')
        assert entry, 'Smoke.cam should have been rejected'

        entry = self.feed.find_entry(title='Smoke.1280x720')
        assert entry, 'entry not found?'
        assert entry in self.feed.accepted, '720p should be accepted'
        assert len(self.feed.rejected) == 2, 'wrong number of entries rejected'
        assert len(self.feed.accepted) == 2, 'wrong number of entries accepted'

    def test_min(self):
        self.execute_feed('min')
        entry = self.feed.find_entry('rejected', title='Smoke.HDTV')
        assert entry, 'Smoke.HDTV should have been rejected'

        entry = self.feed.find_entry(title='Smoke.1280x720')
        assert entry, 'entry not found?'
        assert entry in self.feed.accepted, '720p should be accepted'
        assert len(self.feed.rejected) == 2, 'wrong number of entries rejected'
        assert len(self.feed.accepted) == 2, 'wrong number of entries accepted'

    def test_max(self):
        self.execute_feed('max')
        entry = self.feed.find_entry('rejected', title='Smoke.1280x720')
        assert entry, 'Smoke.1280x720 should have been rejected'

        entry = self.feed.find_entry(title='Smoke.cam')
        assert entry, 'entry not found?'
        assert entry in self.feed.accepted, 'cam should be accepted'
        assert len(self.feed.rejected) == 3, 'wrong number of entries rejected'
        assert len(self.feed.accepted) == 1, 'wrong number of entries accepted'

    def test_min_max(self):
        self.execute_feed('min_max')
        entry = self.feed.find_entry('rejected', title='Smoke.1280x720')
        assert entry, 'Smoke.1280x720 should have been rejected'

        entry = self.feed.find_entry(title='Smoke.HR')
        assert entry, 'entry not found?'
        assert entry in self.feed.accepted, 'HR should be accepted'
        assert len(self.feed.rejected) == 3, 'wrong number of entries rejected'
        assert len(self.feed.accepted) == 1, 'wrong number of entries accepted'
