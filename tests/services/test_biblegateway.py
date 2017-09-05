import pytest
from . import ServiceTest

from erasmus.services import BibleGateway
from erasmus.data import Passage


class TestBibleGateway(ServiceTest):
    @pytest.fixture
    def service(self):
        return BibleGateway({})

    @pytest.fixture
    def good_mock_search(self, mocker, mock_response):
        return_value = '''<html><body>
    <div id="serp-bible-pane" class="iv-pane active">
        <p class="search-total-results">
            50 Bible results for <span class="search-term">&ldquo;one two three&rdquo;</span> Showing results 1-2.
        </p>
        <h4 class="search-result-heading">
            Bible search results
        </h4>
        <div class="search-result-list">
            <div class="text-html">
                <article class="row bible-item">
                    <div class="bible-item-title-wrap col-sm-3">
                        <a class="bible-item-title" href="">John 1:1-4</a>
                    </div>
                    <div class="bible-item-text col-sm-9">Lorem ipsum</div>
                </article>
                <article class="row bible-item">
                    <div class="bible-item-title-wrap col-sm-3">
                        <a class="bible-item-title" href="">Genesis 50:1</a>
                    </div>
                    <div class="bible-item-text col-sm-9">Lorem ipsum</div>
                </article>
            </div>
        </div>
    </div>
</body></html>'''
        mocker.patch.object(mock_response, 'text',
                            new_callable=mocker.AsyncMock,
                            return_value=return_value)

        return mock_response

    @pytest.fixture
    def bad_mock_search(self, mocker, good_mock_search):
        good_mock_search.text.return_value = '''<html>
    <body>
    </body>
</html>'''

        return good_mock_search

    @pytest.fixture
    def search_url(self):
        return f'https://www.biblegateway.com/quicksearch/?quicksearch=one+two+three&qs_version=esv&' \
               'limit=20&interface=print'

    @pytest.fixture
    def good_mock_passages(self, mocker, mock_response):
        return_value = '''<html><body>
<div class="passage-text"><div class='passage-wrap'><div class='passage-content passage-class-0'><div class="version-NASB result-text-style-normal text-html ">
<h1 class="passage-display"> <span class="passage-display-bcv">Galatians 3:10-11</span><span class="passage-display-version">New American Standard Bible (NASB)</span></h1> <p><span id="en-NASB-29113" class="text Gal-3-10"><sup class="versenum">10 </sup>For as many as are of the works of <sup data-fn='#fen-NASB-29113a' class='footnote' data-link='[&lt;a href=&quot;#fen-NASB-29113a&quot; title=&quot;See footnote a&quot;&gt;a&lt;/a&gt;]'>[<a href="#fen-NASB-29113a" title="See footnote a">a</a>]</sup>the Law are under a curse; for it is written, “<sup class='crossreference' data-cr='#cen-NASB-29113A'  data-link='(&lt;a href=&quot;#cen-NASB-29113A&quot; title=&quot;See cross-reference A&quot;&gt;A&lt;/a&gt;)'>(<a href="#cen-NASB-29113A" title="See cross-reference A">A</a>)</sup><span style="font-variant: small-caps" class="small-caps">Cursed is everyone who does not abide by all things written in the book of the law, to perform them</span>.”</span> <span id="en-NASB-29114" class="text Gal-3-11"><sup class="versenum">11 </sup>Now that <sup class='crossreference' data-cr='#cen-NASB-29114B'  data-link='(&lt;a href=&quot;#cen-NASB-29114B&quot; title=&quot;See cross-reference B&quot;&gt;B&lt;/a&gt;)'>(<a href="#cen-NASB-29114B" title="See cross-reference B">B</a>)</sup>no one is justified <sup data-fn='#fen-NASB-29114b' class='footnote' data-link='[&lt;a href=&quot;#fen-NASB-29114b&quot; title=&quot;See footnote b&quot;&gt;b&lt;/a&gt;]'>[<a href="#fen-NASB-29114b" title="See footnote b">b</a>]</sup>by <sup data-fn='#fen-NASB-29114c' class='footnote' data-link='[&lt;a href=&quot;#fen-NASB-29114c&quot; title=&quot;See footnote c&quot;&gt;c&lt;/a&gt;]'>[<a href="#fen-NASB-29114c" title="See footnote c">c</a>]</sup>the Law before God is evident; for, “<sup data-fn='#fen-NASB-29114d' class='footnote' data-link='[&lt;a href=&quot;#fen-NASB-29114d&quot; title=&quot;See footnote d&quot;&gt;d&lt;/a&gt;]'>[<a href="#fen-NASB-29114d" title="See footnote d">d</a>]</sup><sup class='crossreference' data-cr='#cen-NASB-29114C'  data-link='(&lt;a href=&quot;#cen-NASB-29114C&quot; title=&quot;See cross-reference C&quot;&gt;C&lt;/a&gt;)'>(<a href="#cen-NASB-29114C" title="See cross-reference C">C</a>)</sup><span style="font-variant: small-caps" class="small-caps">The righteous man shall live by faith</span>.”</span> </p><div class="footnotes">
<h4>Footnotes:</h4><ol><li id="fen-NASB-29113a"><a href="#en-NASB-29113" title="Go to Galatians 3:10">Galatians 3:10</a> <span class='footnote-text'>Or <i>law</i></span></li>

<li id="fen-NASB-29114b"><a href="#en-NASB-29114" title="Go to Galatians 3:11">Galatians 3:11</a> <span class='footnote-text'>Or <i>in</i></span></li>

<li id="fen-NASB-29114c"><a href="#en-NASB-29114" title="Go to Galatians 3:11">Galatians 3:11</a> <span class='footnote-text'>Or <i>law</i></span></li>

<li id="fen-NASB-29114d"><a href="#en-NASB-29114" title="Go to Galatians 3:11">Galatians 3:11</a> <span class='footnote-text'>Or <i>But he who is righteous by faith shall live</i></span></li>

</ol></div> <!--end of footnotes-->
<div class="crossrefs">
<h4>Cross references:</h4><ol><li id="cen-NASB-29113A"><a href="#en-NASB-29113" title="Go to Galatians 3:10">Galatians 3:10</a> : <a class="crossref-link" href="/passage/?search=Deuteronomy+27%3A26&version=NASB" data-bibleref="Deuteronomy 27:26">Deut 27:26</a></li>

<li id="cen-NASB-29114B"><a href="#en-NASB-29114" title="Go to Galatians 3:11">Galatians 3:11</a> : <a class="crossref-link" href="/passage/?search=Galatians+2%3A16&version=NASB" data-bibleref="Galatians 2:16">Gal 2:16</a></li>

<li id="cen-NASB-29114C"><a href="#en-NASB-29114" title="Go to Galatians 3:11">Galatians 3:11</a> : <a class="crossref-link" href="/passage/?search=Habakkuk+2%3A4%2CRomans+1%3A17%2CHebrews+10%3A38&version=NASB" data-bibleref="Habakkuk 2:4, Romans 1:17, Hebrews 10:38">Hab 2:4; Rom 1:17; Heb 10:38</a></li>

</ol></div> <!--end of crossrefs-->
</div>
<div class="publisher-info-bottom with-single">
<strong><a href="/versions/New-American-Standard-Bible-NASB/">New American Standard Bible</a> (NASB)</strong> <p> Copyright ©  1960, 1962, 1963, 1968, 1971, 1972, 1973, 1975, 1977, 1995 by <a href="http://www.lockman.org/">The Lockman Foundation</a></p></div></div>
</div>
</div>
</body></html>'''  # noqa

        mocker.patch.object(mock_response, 'text',
                            new_callable=mocker.AsyncMock,
                            return_value=return_value)

        return mock_response

    @pytest.fixture
    def bad_mock_passages(self, mocker, good_mock_passages):
        good_mock_passages.text.return_value = '''<html>
    <body>
    </body>
</html>'''

        return good_mock_passages

    def get_passages_url(self, version: str, passage: Passage) -> str:
        passage_str = str(passage).replace(' ', '+').replace(':', '%3A')
        return f'https://www.biblegateway.com/passage/?search={passage_str}&version={version}&interface=print'
