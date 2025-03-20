#!/usr/bin/env python3
import os
import shutil
import argparse
import json
import requests
import time
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, ID3NoHeaderError, APIC
from io import BytesIO
from PIL import Image
from urllib.parse import quote

def extract_and_save_album_art_mp3(file_path, album_dir):
    """Extract and save album art from an MP3 file."""
    try:
        audio = ID3(file_path)
        for tag in audio.values():
            if tag.FrameID.startswith('APIC'):  # Album art
                artwork_data = tag.data
                img = Image.open(BytesIO(artwork_data))
                
                # Save the image as cover.jpg in the album directory
                art_path = album_dir / "cover.jpg"
                
                # Only save if the cover doesn't already exist
                if not art_path.exists():
                    img.save(art_path)
                    print(f"Album art saved to {art_path}")
                return True
        return False
    except Exception as e:
        print(f"Error extracting album art from MP3 {file_path}: {e}")
        return False

def extract_and_save_album_art_m4a(file_path, album_dir):
    """Extract and save album art from an M4A file."""
    try:
        audio = MP4(file_path)
        if 'covr' in audio:
            artwork_data = audio['covr'][0]
            img = Image.open(BytesIO(artwork_data))
            
            # Save the image as cover.jpg in the album directory
            art_path = album_dir / "cover.jpg"
            
            # Only save if the cover doesn't already exist
            if not art_path.exists():
                img.save(art_path)
                print(f"Album art saved to {art_path}")
            return True
        return False
    except Exception as e:
        print(f"Error extracting album art from M4A {file_path}: {e}")
        return False

def extract_metadata_mp3(file_path):
    """Extract metadata from an MP3 file."""
    try:
        audio = EasyID3(file_path)
        print(f"Full metadata for {file_path}:")
        for key, value in audio.items():
            print(f"  {key}: {value}")
            
        # Extract basic metadata
        title = audio.get('title', ['Unknown Title'])[0]
        artist = audio.get('artist', ['Unknown Artist'])[0]
        
        # If album is not available, use the original filename as a fallback
        if 'album' in audio:
            album = audio['album'][0]
        else:
            # Try to extract potential album name from original filename
            orig_name = Path(file_path).stem
            # If the title appears in the filename, the rest might be the album
            if title.lower() in orig_name.lower():
                album = orig_name.replace(title, "").strip()
                if not album:  # If nothing left, use original name
                    album = "Unknown Album"
            else:
                album = "Unknown Album"
            print(f"  No album metadata, using: {album}")
            
        metadata = {
            'title': title,
            'artist': artist,
            'album': album
        }
        return metadata
    except ID3NoHeaderError:
        print(f"No ID3 header found for {file_path}")
        return {
            'title': Path(file_path).stem,
            'artist': 'Unknown Artist',
            'album': 'Unknown Album'
        }
    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
        return {
            'title': Path(file_path).stem,
            'artist': 'Unknown Artist',
            'album': 'Unknown Album'
        }

def extract_metadata_m4a(file_path):
    """Extract metadata from an M4A file."""
    try:
        audio = MP4(file_path)
        print(f"Full metadata for {file_path}:")
        for key, value in audio.items():
            print(f"  {key}: {value}")
        
        # Extract basic metadata using M4A tags
        # M4A tags are different from MP3 tags
        title = "Unknown Title"
        artist = "Unknown Artist"
        album = "Unknown Album"
        
        # Title
        if '©nam' in audio:
            title = audio['©nam'][0]
        
        # Artist
        if '©ART' in audio:
            artist = audio['©ART'][0]
        elif 'aART' in audio:
            artist = audio['aART'][0]
        
        # Album
        if '©alb' in audio:
            album = audio['©alb'][0]
            
        metadata = {
            'title': title,
            'artist': artist,
            'album': album
        }
        
        print(f"Extracted metadata from M4A: {metadata}")
        return metadata
    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
        return {
            'title': Path(file_path).stem,
            'artist': 'Unknown Artist',
            'album': 'Unknown Album'
        }

def extract_metadata(file_path):
    """Extract metadata from an audio file based on file extension."""
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.mp3':
        return extract_metadata_mp3(file_path)
    elif file_ext == '.m4a':
        return extract_metadata_m4a(file_path)
    else:
        print(f"Unsupported file format: {file_ext}")
        return {
            'title': Path(file_path).stem,
            'artist': 'Unknown Artist',
            'album': 'Unknown Album'
        }

def extract_and_save_album_art(file_path, album_dir):
    """Extract and save album art based on file extension."""
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.mp3':
        return extract_and_save_album_art_mp3(file_path, album_dir)
    elif file_ext == '.m4a':
        return extract_and_save_album_art_m4a(file_path, album_dir)
    else:
        print(f"Unsupported file format for album art extraction: {file_ext}")
        return False

def clean_empty_unknown_album_folders(base_dir, simulate=False):
    """
    Remove empty 'Unknown Album' folders.
    Returns the number of folders removed.
    """
    removed_count = 0
    
    for artist_dir in base_dir.iterdir():
        if not artist_dir.is_dir():
            continue
            
        unknown_album_dir = artist_dir / "Unknown Album"
        if not unknown_album_dir.exists() or not unknown_album_dir.is_dir():
            continue
        
        # Check if the Unknown Album folder is empty
        # Get a list of all files/folders in the directory, excluding hidden files
        items = [f for f in unknown_album_dir.iterdir() if not f.name.startswith('.')]
        
        if len(items) == 0:
            print(f"Found empty 'Unknown Album' folder: {unknown_album_dir}")
            if not simulate:
                try:
                    unknown_album_dir.rmdir()
                    print(f"Removed empty folder: {unknown_album_dir}")
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing folder {unknown_album_dir}: {e}")
            else:
                print(f"[SIMULATE] Would remove: {unknown_album_dir}")
                removed_count += 1
    
    return removed_count

def sanitize_filename(name):
    """Remove invalid characters from filename."""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name

def search_album_info(artist, title):
    """
    Search for album information using the MusicBrainz API.
    Returns album name or None if not found.
    Uses scoring and release type information to select the most accurate album.
    """
    try:
        print(f"Searching for album information for: {artist} - {title}")
        
        # MusicBrainz API requires a delay between requests
        time.sleep(1)
        
        # Construct the URL for the MusicBrainz API
        base_url = "https://musicbrainz.org/ws/2/recording/"
        query = f"?query=artist:{artist}+recording:{title}&fmt=json"
        url = base_url + query
        
        # Add a user agent header to be a good API citizen
        headers = {
            "User-Agent": "I-MusicExtractor/1.0 (https://github.com/yourname/I-MusicExtractor)"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we found any recordings
            if "recordings" in data and len(data["recordings"]) > 0:
                # Sort recordings by score (highest first)
                sorted_recordings = sorted(data["recordings"], key=lambda x: int(x.get("score", 0)), reverse=True)
                
                print(f"Found {len(sorted_recordings)} matching recordings, sorted by score")
                
                best_album = None
                best_album_score = 0
                best_album_info = None
                
                # First pass: try to find official studio albums
                for recording in sorted_recordings:
                    recording_score = int(recording.get("score", 0))
                    
                    # Skip low-confidence matches
                    if recording_score < 50:
                        continue
                        
                    if "releases" in recording and len(recording["releases"]) > 0:
                        # Sort releases by priority:
                        # 1. Official releases
                        # 2. Albums (not singles or compilations)
                        # 3. Earliest release date
                        for release in recording["releases"]:
                            # Calculate a score for this release
                            release_score = recording_score
                            
                            # Prioritize official releases
                            if "status" in release and release["status"] == "Official":
                                release_score += 30
                            
                            # Prioritize albums over singles/compilations
                            if "release-group" in release:
                                if release["release-group"].get("primary-type") == "Album":
                                    release_score += 20
                                    
                                    # Deprioritize compilations
                                    if "secondary-types" in release["release-group"]:
                                        if "Compilation" in release["release-group"]["secondary-types"]:
                                            release_score -= 15
                            
                            # If this is the best match so far, store it
                            if release_score > best_album_score:
                                best_album = release["title"]
                                best_album_score = release_score
                                best_album_info = {
                                    "title": release["title"],
                                    "score": release_score,
                                    "status": release.get("status", "Unknown"),
                                    "type": release.get("release-group", {}).get("primary-type", "Unknown"),
                                    "date": release.get("date", "Unknown")
                                }
                
                # If we found a good album match, return it
                if best_album and best_album_score > 70:
                    print(f"Found best album match: {best_album} (score: {best_album_score})")
                    print(f"Album details: {best_album_info}")
                    return best_album
                
                # If we didn't find a good match, just return the first release as before
                if "releases" in sorted_recordings[0] and len(sorted_recordings[0]["releases"]) > 0:
                    album_name = sorted_recordings[0]["releases"][0]["title"]
                    print(f"No high-confidence album match, using first result: {album_name}")
                    return album_name
        
        # Alternative API: Last.fm (in case MusicBrainz doesn't find results)
        # Default Last.fm API key
        default_api_key = "9c35564869e327244fb02a6949ef5a63"
        
        # Check if Last.fm API key is available in environment variables (override default)
        api_key = os.environ.get("LASTFM_API_KEY", default_api_key)
        
        # Add autocorrect=1 to use Last.fm's correction system
        last_fm_url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={artist}&track={title}&autocorrect=1&format=json"
        
        response = requests.get(last_fm_url)
        if response.status_code == 200:
            data = response.json()
            if "track" in data and "album" in data["track"]:
                album_name = data["track"]["album"]["title"]
                print(f"Found album from Last.fm: {album_name}")
                return album_name
        
        print(f"No album information found for {artist} - {title}")
        return None
    
    except Exception as e:
        print(f"Error searching for album information: {e}")
        return None

def search_wiki_album_art(artist, album):
    """
    Search for album art using Wikipedia API directly.
    Returns image data (bytes) if found, None otherwise.
    """
    try:
        print(f"Searching Wikipedia directly for album art: {artist} - {album}")
        
        # Define headers for all requests to Wikipedia/Wikimedia
        headers = {
            "User-Agent": "I-MusicExtractor/1.0 (https://github.com/yourname/I-MusicExtractor; your-email@example.com) Python-Requests/2.28.1"
        }
        
        # Step 1: Search for the album page on Wikipedia
        search_term = f"{artist} {album} album"
        wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(search_term)}&format=json"
        
        print(f"Wikipedia search URL: {wiki_search_url}")
        response = requests.get(wiki_search_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            search_results = data.get('query', {}).get('search', [])
            
            if not search_results:
                print("No Wikipedia search results found.")
                return None
                
            # Get the page ID of the first result
            page_id = search_results[0]['pageid']
            print(f"Found Wikipedia page ID: {page_id}")
            
            # Step 2: Get the images on that page
            wiki_images_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=images&pageids={page_id}&format=json"
            
            response = requests.get(wiki_images_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                pages = data.get('query', {}).get('pages', {})
                
                if str(page_id) in pages:
                    images = pages[str(page_id)].get('images', [])
                    print(f"Found {len(images)} images on Wikipedia page")
                    
                    if not images:
                        print("No images found on the Wikipedia page.")
                        return None
                    
                    # Look for likely album cover images
                    cover_keywords = ['cover', 'album', 'front', 'artwork', 'art']
                    potential_covers = []
                    
                    for image in images:
                        image_title = image['title'].lower()
                        # Skip File: prefix for scoring but keep it for the API request
                        image_title_clean = image_title
                        if 'file:' in image_title:
                            image_title_clean = image_title.split('file:')[-1].strip()
                            
                        # Score the image based on likelihood of being an album cover
                        score = 0
                        for keyword in cover_keywords:
                            if keyword in image_title_clean:
                                score += 1
                                
                        # Add artist or album name match bonus
                        if artist.lower() in image_title_clean:
                            score += 2
                        if album.lower() in image_title_clean:
                            score += 3
                            
                        # Prioritize JPG and PNG files
                        if image_title_clean.endswith('.jpg') or image_title_clean.endswith('.jpeg'):
                            score += 2
                        elif image_title_clean.endswith('.png'):
                            score += 1
                            
                        if score > 0:
                            potential_covers.append((image['title'], score))
                    
                    # Sort by score, highest first
                    potential_covers.sort(key=lambda x: x[1], reverse=True)
                    print(f"Found {len(potential_covers)} potential album covers")
                    
                    # Try to get image info for each potential cover
                    for cover_title, score in potential_covers:
                        print(f"Trying potential cover: {cover_title} (score: {score})")
                        
                        # Get the image info (including URL)
                        image_info_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={quote(cover_title)}&prop=imageinfo&iiprop=url|size&format=json"
                        
                        print(f"Image info URL: {image_info_url}")
                        response = requests.get(image_info_url, headers=headers)
                        print(f"Image info response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            pages = data.get('query', {}).get('pages', {})
                            print(f"Image info pages: {pages.keys()}")
                            
                            for page_id, page_info in pages.items():
                                if 'imageinfo' in page_info:
                                    for img_info in page_info['imageinfo']:
                                        if 'url' in img_info:
                                            image_url = img_info['url']
                                            print(f"Found album art URL from Wikipedia: {image_url}")
                                            
                                            # Download the image with proper headers
                                            try:
                                                print(f"Downloading image from: {image_url}")
                                                img_response = requests.get(image_url, headers=headers)
                                                print(f"Image download status: {img_response.status_code}")
                                                
                                                if img_response.status_code == 200:
                                                    content_length = len(img_response.content)
                                                    print(f"Successfully downloaded image ({content_length} bytes)")
                                                    
                                                    # Success! Return the image data
                                                    return img_response.content
                                                else:
                                                    print(f"Failed to download image: HTTP {img_response.status_code}")
                                            except Exception as download_error:
                                                print(f"Error downloading image: {download_error}")
                                        else:
                                            print("No URL found in imageinfo")
                                else:
                                    print(f"No imageinfo found for page {page_id}")
        
        # If we get here, we didn't find any suitable images
        print("No album art found on Wikipedia.")
        return None
        
    except Exception as e:
        print(f"Error searching Wikipedia for album art: {e}")
        return None

def search_album_art_online(artist, album, title):
    """
    Search for album art online using Last.fm API and fallback to other sources if needed.
    Returns image data (bytes) if found, None otherwise.
    """
    try:
        print(f"Searching for album art online for: {artist} - {album} - {title}")
        
        # Default Last.fm API key
        default_api_key = "9c35564869e327244fb02a6949ef5a63"
        
        # Check if Last.fm API key is available in environment variables (override default)
        api_key = os.environ.get("LASTFM_API_KEY", default_api_key)
            
        # Try searching by album first (if available)
        if album and album != "Unknown Album":
            album_url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={api_key}&artist={artist}&album={album}&format=json"
            
            response = requests.get(album_url)
            if response.status_code == 200:
                data = response.json()
                if "album" in data and "image" in data["album"]:
                    # Last.fm returns multiple image sizes - get the largest one
                    for img in reversed(data["album"]["image"]):  # Reversed to get largest first
                        if img["#text"] and img["size"] in ["extralarge", "mega"]:
                            image_url = img["#text"]
                            print(f"Found album art from Last.fm album search: {image_url}")
                            
                            # Download the image
                            img_response = requests.get(image_url)
                            if img_response.status_code == 200:
                                return img_response.content
        
        # If no album art found by album, try by track
        track_url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={artist}&track={title}&format=json"
        
        response = requests.get(track_url)
        if response.status_code == 200:
            data = response.json()
            if "track" in data and "album" in data["track"] and "image" in data["track"]["album"]:
                # Get the largest image
                for img in reversed(data["track"]["album"]["image"]):
                    if img["#text"] and img["size"] in ["extralarge", "mega"]:
                        image_url = img["#text"]
                        print(f"Found album art from Last.fm track search: {image_url}")
                        
                        # Download the image
                        img_response = requests.get(image_url)
                        if img_response.status_code == 200:
                            return img_response.content
        
        # If Last.fm failed, try Wikipedia as fallback
        print(f"Last.fm search failed, trying Wikipedia for {artist} - {album}")
        wiki_result = search_wiki_album_art(artist, album)
        if wiki_result:
            return wiki_result
            
        # If all methods failed, try DBpedia as a last resort
        print(f"Wikipedia search failed, trying DBpedia for {artist} - {album}")
        
        # Step 1: Find the album using DBpedia SPARQL endpoint - simplified query
        sparql_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX dbpedia2: <http://dbpedia.org/property/>
            PREFIX owl: <http://dbpedia.org/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?name, ?coverArtVar WHERE {{
                ?subject rdf:type <http://dbpedia.org/ontology/Album> .
                ?subject dbpedia2:cover ?coverArtVar .
                ?subject ?p ?artist_obj .
                ?artist_obj rdfs:label ?artist_name .
                FILTER(CONTAINS(LCASE(?artist_name), LCASE("{artist}")))
                ?subject rdfs:label ?name .
                FILTER(CONTAINS(LCASE(?name), LCASE("{album}")))
            }}
            LIMIT 10
        """
        
        # URL encode the SPARQL query
        encoded_query = quote(sparql_query)
        
        # Make request to DBpedia SPARQL endpoint
        dbpedia_url = f"http://dbpedia.org/sparql?format=JSON&default-graph-uri=http%3A%2F%2Fdbpedia.org&query={encoded_query}"
        
        print(f"Querying DBpedia with URL: {dbpedia_url[:100]}...")
        response = requests.get(dbpedia_url, headers={'Accept': 'application/json'})
        
        print(f"DBpedia response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', {}).get('bindings', [])
            
            print(f"DBpedia results found: {len(results)}")
            
            if results:
                # Get the cover art filename from the first result
                cover_filename = None
                for result in results:
                    print(f"Result: {result}")
                    if 'coverArtVar' in result:
                        # Extract the filename from the value
                        cover_art_value = result['coverArtVar']['value']
                        print(f"Cover art value: {cover_art_value}")
                        # Might be a full URI or just filename
                        if '/' in cover_art_value:
                            cover_filename = cover_art_value.split('/')[-1]
                        else:
                            cover_filename = cover_art_value
                        
                        # Remove any @en or quotes
                        cover_filename = cover_filename.strip('@en').strip('"')
                        break
                
                if cover_filename:
                    print(f"Found cover art filename from DBpedia: {cover_filename}")
                    
                    # Step 2: Use Wikipedia API to get the actual image URL
                    wiki_api_url = f"http://en.wikipedia.org/w/api.php?format=json&action=query&prop=imageinfo&iiprop=url|size&titles=File:{cover_filename}"
                    
                    print(f"Querying Wikipedia API with URL: {wiki_api_url}")
                    response = requests.get(wiki_api_url)
                    print(f"Wikipedia API response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"Wikipedia API response: {data}")
                        pages = data.get('query', {}).get('pages', {})
                        
                        # Extract the image URL from the response
                        for page_id, page_info in pages.items():
                            if 'imageinfo' in page_info:
                                for img_info in page_info['imageinfo']:
                                    if 'url' in img_info:
                                        image_url = img_info['url']
                                        print(f"Found album art URL from Wikipedia: {image_url}")
                                        
                                        # Download the image
                                        img_response = requests.get(image_url)
                                        if img_response.status_code == 200:
                                            return img_response.content
                                        else:
                                            print(f"Failed to download image: {img_response.status_code}")
                    else:
                        print(f"Wikipedia API error response: {response.text}")
            else:
                print("No results found from DBpedia query")
        else:
            print(f"DBpedia error response: {response.text}")
        
        # Try a more generic DBpedia query as a last resort
        print("Trying a more generic DBpedia query...")
        sparql_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dbr: <http://dbpedia.org/resource/>
            
            SELECT ?album ?cover WHERE {{
              ?album a dbo:Album ;
                     foaf:name ?albumName ;
                     dbo:cover ?cover .
              FILTER(CONTAINS(LCASE(STR(?albumName)), LCASE("{album}")))
            }}
            LIMIT 5
        """
        
        encoded_query = quote(sparql_query)
        dbpedia_url = f"http://dbpedia.org/sparql?format=JSON&default-graph-uri=http%3A%2F%2Fdbpedia.org&query={encoded_query}"
        
        print(f"Querying DBpedia with generic query URL: {dbpedia_url[:100]}...")
        response = requests.get(dbpedia_url, headers={'Accept': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', {}).get('bindings', [])
            
            print(f"Generic DBpedia results found: {len(results)}")
            
            if results:
                for result in results:
                    if 'cover' in result:
                        cover_art_value = result['cover']['value']
                        print(f"Generic query cover art value: {cover_art_value}")
                        
                        # Extract the filename
                        if '/' in cover_art_value:
                            cover_filename = cover_art_value.split('/')[-1]
                        else:
                            cover_filename = cover_art_value
                        
                        # Build Wikipedia API URL
                        wiki_api_url = f"http://en.wikipedia.org/w/api.php?format=json&action=query&prop=imageinfo&iiprop=url|size&titles=File:{cover_filename}"
                        
                        print(f"Querying Wikipedia API from generic query: {wiki_api_url}")
                        response = requests.get(wiki_api_url)
                        
                        if response.status_code == 200:
                            data = response.json()
                            pages = data.get('query', {}).get('pages', {})
                            
                            for page_id, page_info in pages.items():
                                if 'imageinfo' in page_info:
                                    for img_info in page_info['imageinfo']:
                                        if 'url' in img_info:
                                            image_url = img_info['url']
                                            print(f"Found album art URL from generic query: {image_url}")
                                            
                                            img_response = requests.get(image_url)
                                            if img_response.status_code == 200:
                                                return img_response.content
        
        print(f"No album art found online for {artist} - {album} - {title}")
        return None
    
    except Exception as e:
        print(f"Error searching for album art online: {e}")
        return None

def find_and_organize_unknowns(base_dir, extract_art=False, simulate=False, clean_empty=True):
    """
    Find songs in 'Unknown Album' folders and attempt to find their album information,
    then reorganize them accordingly.
    """
    # Track statistics
    total_unknown_files = 0
    files_with_found_albums = 0
    
    # Create a dictionary to store album information already found
    # This helps avoid repeated API calls for the same song
    album_cache = {}
    
    for artist_dir in base_dir.iterdir():
        if not artist_dir.is_dir():
            continue
            
        unknown_album_dir = artist_dir / "Unknown Album"
        if not unknown_album_dir.exists() or not unknown_album_dir.is_dir():
            continue
            
        print(f"\nProcessing Unknown Album folder for artist: {artist_dir.name}")
        
        for file in unknown_album_dir.glob("*.*"):
            if file.suffix.lower() not in ['.mp3', '.m4a']:
                continue
                
            total_unknown_files += 1
            print(f"\nExamining file: {file}")
            
            # Extract metadata to get artist and title
            metadata = extract_metadata(file)
            
            artist = metadata['artist']
            title = metadata['title']
            
            # Create a cache key
            cache_key = f"{artist}|{title}"
            
            # Check if we already have this song's album information
            if cache_key in album_cache:
                album = album_cache[cache_key]
                print(f"Using cached album information: {album}")
            else:
                # Search for album information
                album = search_album_info(artist, title)
                
                if album:
                    album_cache[cache_key] = album
                else:
                    print(f"Could not find album information for {artist} - {title}")
                    continue
            
            # If we found album information, reorganize the file
            if album and album != "Unknown Album":
                files_with_found_albums += 1
                
                # Sanitize the album name
                album_name = sanitize_filename(album)
                
                # Create the destination album directory
                album_dir = artist_dir / album_name
                if not album_dir.exists():
                    if not simulate:
                        os.makedirs(album_dir)
                    print(f"Created album directory: {album_dir}")
                    
                # Extract album art if requested
                if extract_art and not simulate:
                    extract_and_save_album_art(file, album_dir)
                
                # Move the file to the new album directory
                dest_path = album_dir / file.name
                if not simulate:
                    shutil.move(file, dest_path)
                print(f"Moved '{file.name}' to '{dest_path}'")
    
    # Clean up empty Unknown Album folders if requested
    removed_folders = 0
    if clean_empty and not simulate:
        print("\nCleaning up empty 'Unknown Album' folders...")
        removed_folders = clean_empty_unknown_album_folders(base_dir, simulate)
    elif clean_empty and simulate:
        print("\n[SIMULATE] Checking for empty 'Unknown Album' folders...")
        removed_folders = clean_empty_unknown_album_folders(base_dir, simulate)
    
    # Print summary
    print("\n" + "="*50)
    print(f"Found {total_unknown_files} files in Unknown Album folders")
    print(f"Successfully found album information for {files_with_found_albums} files")
    print(f"Moved {files_with_found_albums} files to their proper album folders")
    if clean_empty:
        print(f"Removed {removed_folders} empty 'Unknown Album' folders")
    print("="*50)
    
    return files_with_found_albums

def find_and_attach_album_art(base_dir, simulate=False, use_folder_structure=True):
    """
    Find songs without album art, search for album art online, and attach it to the files.
    Returns the number of files updated with album art.
    
    Parameters:
    - base_dir: Base directory containing the organized music
    - simulate: If True, only simulate actions without making changes
    - use_folder_structure: If True, use folder structure to determine artist/album instead of file metadata
    """
    # Track statistics
    total_files = 0
    files_without_art = 0
    files_updated = 0
    files_failed = 0
    files_moved = 0
    
    print(f"\nScanning for files without album art in {base_dir}")
    
    # Create a dictionary to store album art already found
    # This helps avoid repeated API calls for the same album
    art_cache = {}
    album_cache = {}
    
    # Walk through all directories
    for root, dirs, files in os.walk(base_dir):
        root_path = Path(root)
        
        # Skip the root directory itself
        if root_path == base_dir:
            continue
            
        # Process each music file
        for file in files:
            file_path = root_path / file
            file_ext = file_path.suffix.lower()
            
            if file_ext not in ['.mp3', '.m4a']:
                continue
                
            total_files += 1
            
            try:
                # Check if the file already has album art
                if has_album_art(file_path):
                    print(f"File already has album art: {file_path}")
                    continue
                    
                files_without_art += 1
                print(f"\nExamining file without album art: {file_path}")
                
                # Get artist and album from folder structure or file metadata
                if use_folder_structure:
                    # Extract artist and album from path
                    # Expected structure: base_dir/Artist/Album/song.mp3
                    parts = file_path.parts
                    if len(parts) >= 3:  # Enough parts for base/artist/album/file
                        # Start from the end and work backwards
                        # -1 is the file, -2 is album, -3 is artist
                        album = parts[-2]
                        artist = parts[-3]
                        
                        # If we're at base_dir/Artist/song.mp3, album would be Unknown Album
                        if artist == base_dir.name:
                            artist = album
                            album = "Unknown Album"
                            
                        # Extract title from filename without extension
                        title = file_path.stem
                        
                        print(f"Using folder structure: Artist={artist}, Album={album}, Title={title}")
                    else:
                        # Fall back to metadata if path structure is unexpected
                        print(f"Folder structure not as expected, falling back to file metadata")
                        metadata = extract_metadata(file_path)
                        artist = metadata['artist']
                        album = metadata['album']
                        title = metadata['title']
                else:
                    # Use file metadata
                    metadata = extract_metadata(file_path)
                    artist = metadata['artist']
                    album = metadata['album']
                    title = metadata['title']
                
                # Check if the file is in an "Unknown Album" folder
                is_in_unknown_album = False
                if "Unknown Album" in str(file_path):
                    is_in_unknown_album = True
                    print(f"File is in 'Unknown Album' folder, will attempt to find correct album")
                
                # Create a cache key
                cache_key = f"{artist}|{album}"
                
                # Check if we already have album art for this artist/album
                image_data = None
                if cache_key in art_cache:
                    print(f"Using cached album art for {artist} - {album}")
                    image_data = art_cache[cache_key]
                else:
                    # Search for album art online
                    image_data = search_album_art_online(artist, album, title)
                    
                    if image_data:
                        # Cache the album art
                        art_cache[cache_key] = image_data
                        print(f"Found and cached album art for {artist} - {album}")
                    else:
                        print(f"Could not find album art online for {artist} - {album} - {title}")
                        continue
                
                # If we found album art, attach it to the file
                if image_data:
                    if not simulate:
                        if attach_album_art(file_path, image_data):
                            files_updated += 1
                            print(f"Successfully attached album art to: {file_path}")
                            
                            # If the file is in an "Unknown Album" folder, try to find the correct album
                            if is_in_unknown_album:
                                real_album = None
                                
                                # Check if we already searched for this song's album
                                artist_title_key = f"{artist}|{title}"
                                if artist_title_key in album_cache:
                                    real_album = album_cache[artist_title_key]
                                    print(f"Using cached album information: {real_album}")
                                else:
                                    # Search for album information
                                    real_album = search_album_info(artist, title)
                                    
                                    if real_album:
                                        album_cache[artist_title_key] = real_album
                                        print(f"Found album information for {artist} - {title}: {real_album}")
                                    else:
                                        print(f"Could not find album information for {artist} - {title}")
                                
                                # If we found real album information, move the file
                                if real_album and real_album != "Unknown Album":
                                    # Get the artist directory
                                    artist_dir = file_path.parent.parent
                                    
                                    # Sanitize the album name
                                    album_name = sanitize_filename(real_album)
                                    
                                    # Create the destination album directory if it doesn't exist
                                    album_dir = artist_dir / album_name
                                    if not album_dir.exists():
                                        os.makedirs(album_dir)
                                        print(f"Created album directory: {album_dir}")
                                    
                                    # Move the file to the new album directory
                                    dest_path = album_dir / file_path.name
                                    
                                    # Check if destination already exists
                                    if dest_path.exists():
                                        print(f"Destination file already exists: {dest_path}. Skipping move.")
                                    else:
                                        # Move the file
                                        shutil.move(file_path, dest_path)
                                        print(f"Moved file from Unknown Album to {album_name}: {dest_path}")
                                        files_moved += 1
                        else:
                            files_failed += 1
                            print(f"Failed to attach album art to: {file_path}")
                    else:
                        print(f"[SIMULATE] Would attach album art to {file_path}")
                        files_updated += 1
                        
                        # If the file is in an "Unknown Album" folder, simulate finding the correct album
                        if is_in_unknown_album:
                            print(f"[SIMULATE] Would search for album information and potentially move from Unknown Album")
                            # We don't actually search in simulation mode to avoid API calls
            except Exception as e:
                files_failed += 1
                print(f"Error processing file {file_path}: {e}")
                continue
    
    # Print summary
    print("\n" + "="*50)
    print(f"Scanned {total_files} files")
    print(f"Found {files_without_art} files without album art")
    print(f"Successfully attached album art to {files_updated} files")
    if files_moved > 0:
        print(f"Moved {files_moved} files from 'Unknown Album' to proper album folders")
    if files_failed > 0:
        print(f"Failed to attach album art to {files_failed} files")
    print("="*50)
    
    # Return if any files were moved from Unknown Album
    return files_updated, files_moved

def attach_album_art_to_mp3(file_path, image_data):
    """
    Attach album art to an MP3 file.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"Attaching album art to MP3 file: {file_path}")
        
        # Try to open existing ID3 tags
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            # If no ID3 header exists, create one
            print(f"No ID3 header found for {file_path}, creating new tags")
            audio = ID3()
            
            # Extract basic metadata to add to the tags
            try:
                easyid3 = EasyID3(file_path)
                # Copy existing tags if available
            except ID3NoHeaderError:
                # If EasyID3 also fails, create it too
                easyid3 = EasyID3()
                easyid3['title'] = Path(file_path).stem
                
            # Save the basic tags first
            easyid3.save(file_path)
            
            # Reload the tags
            audio = ID3(file_path)
        
        # Create APIC frame for the image
        audio['APIC'] = APIC(
            encoding=3,  # UTF-8
            mime='image/jpeg',
            type=3,  # Front cover
            desc='Cover',
            data=image_data
        )
        
        # Save the changes
        audio.save(file_path)
        print(f"Album art attached to {file_path}")
        return True
        
    except Exception as e:
        print(f"Error attaching album art to MP3 {file_path}: {e}")
        return False

def attach_album_art_to_m4a(file_path, image_data):
    """
    Attach album art to an M4A file.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"Attaching album art to M4A file: {file_path}")
        
        try:
            # Open the file
            audio = MP4(file_path)
            
            # M4A files store cover art as a list of "covr" atoms
            covr = []
            covr.append(image_data)
            audio['covr'] = covr
            
            # Save the changes
            audio.save()
            print(f"Album art attached to {file_path}")
            return True
        except Exception as e:
            print(f"Error with MP4 tags in {file_path}: {e}")
            # Try again with a fresh approach
            audio = MP4(file_path)
            audio.tags = audio.tags or {}
            covr = []
            covr.append(image_data)
            audio['covr'] = covr
            audio.save()
            print(f"Album art attached after retry to {file_path}")
            return True
        
    except Exception as e:
        print(f"Error attaching album art to M4A {file_path}: {e}")
        return False

def attach_album_art(file_path, image_data):
    """
    Attach album art to a music file based on its extension.
    Returns True if successful, False otherwise.
    """
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.mp3':
        return attach_album_art_to_mp3(file_path, image_data)
    elif file_ext == '.m4a':
        return attach_album_art_to_m4a(file_path, image_data)
    else:
        print(f"Unsupported file format for attaching album art: {file_ext}")
        return False

def has_album_art(file_path):
    """
    Check if a file already has album art.
    Returns True if it has album art, False otherwise.
    """
    file_ext = file_path.suffix.lower()
    
    try:
        if file_ext == '.mp3':
            try:
                # Check for album art in MP3
                audio = ID3(file_path)
                for tag in audio.values():
                    if tag.FrameID.startswith('APIC'):  # Album art
                        return True
                return False
            except ID3NoHeaderError:
                # No ID3 header found, so definitely no album art
                return False
        elif file_ext == '.m4a':
            # Check for album art in M4A
            audio = MP4(file_path)
            if 'covr' in audio and audio['covr']:
                return True
            return False
        else:
            print(f"Unsupported file format for checking album art: {file_ext}")
            return False
    except Exception as e:
        print(f"Error checking album art for {file_path}: {e}")
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract and organize audio files based on metadata.')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying them')
    parser.add_argument('-s', '--source-dir', default='Music_to_extract', 
                        help='Source directory containing audio files (relative or absolute path)')
    parser.add_argument('-d', '--dest-name', default='Extracted Music', 
                        help='Name of the destination folder on desktop')
    parser.add_argument('--extract-art', action='store_true', help='Extract and save album artwork')
    parser.add_argument('--force', action='store_true', help='Force overwrite existing duplicates')
    parser.add_argument('--find-unknowns', action='store_true', help='Find and organize songs in Unknown Album folders')
    parser.add_argument('--simulate', action='store_true', help='Simulate actions without making changes (dry run)')
    parser.add_argument('--keep-empty', action='store_true', help='Keep empty Unknown Album folders')
    parser.add_argument('--clean-empty', action='store_true', help='Only clean empty Unknown Album folders')
    parser.add_argument('--find-art', action='store_true', help='Find and attach album art to files that lack it')
    parser.add_argument('--attach-art', action='store_true', help='Attach album art to metadata when extracting or finding album info')
    parser.add_argument('--use-folders', action='store_true', help='Use folder structure instead of file metadata for artist/album info')
    args = parser.parse_args()
    
    # Destination directory path (used by multiple operations)
    desktop_path = Path.home() / "Desktop"
    dest_dir = desktop_path / args.dest_name
    
    # If find-art is specified, only perform that operation
    if args.find_art:
        if not dest_dir.exists():
            print(f"Error: Destination directory {dest_dir} does not exist.")
            return
            
        print(f"Finding and attaching album art for files in {dest_dir}")
        files_updated, files_moved = find_and_attach_album_art(dest_dir, args.simulate, args.use_folders)
        
        # Clean up empty Unknown Album folders if not keeping empty folders
        # Note: We always check for empty folders, not just when files were moved
        if not args.keep_empty and not args.simulate:
            print("\nCleaning up empty 'Unknown Album' folders...")
            removed = clean_empty_unknown_album_folders(dest_dir, False)
            if removed > 0:
                print(f"Removed {removed} empty 'Unknown Album' folders")
            else:
                print("No empty 'Unknown Album' folders found to remove")
        return
    
    # If clean-empty is specified, only perform that operation
    if args.clean_empty:
        if not dest_dir.exists():
            print(f"Error: Destination directory {dest_dir} does not exist.")
            return
            
        print(f"Cleaning empty 'Unknown Album' folders in {dest_dir}")
        removed = clean_empty_unknown_album_folders(dest_dir, args.simulate)
        print(f"Removed {removed} empty 'Unknown Album' folders")
        return
    
    # If find-unknowns is specified, only perform that operation
    if args.find_unknowns:
        if not dest_dir.exists():
            print(f"Error: Destination directory {dest_dir} does not exist.")
            return
            
        print(f"Searching for songs in Unknown Album folders in {dest_dir}")
        find_and_organize_unknowns(dest_dir, args.extract_art, args.simulate, args.clean_empty)
        
        # If attach-art option is specified, find and attach album art after reorganizing
        if args.attach_art and not args.simulate:
            print("\nNow searching for and attaching album art...")
            files_updated, files_moved = find_and_attach_album_art(dest_dir, args.simulate, args.use_folders)
            
            # Clean up empty Unknown Album folders if not keeping empty folders
            if not args.keep_empty:
                print("\nCleaning up empty 'Unknown Album' folders...")
                removed = clean_empty_unknown_album_folders(dest_dir, False)
                if removed > 0:
                    print(f"Removed {removed} empty 'Unknown Album' folders")
                else:
                    print("No empty 'Unknown Album' folders found to remove")
            
        return
    
    # Source directory with audio files - handle both relative and absolute paths
    source_path = args.source_dir
    
    # Convert to Path object, respecting absolute paths
    if os.path.isabs(source_path):
        source_dir = Path(source_path)
    else:
        source_dir = Path(source_path)
    
    # Verify source directory exists
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"Error: Source directory '{source_dir}' does not exist or is not a directory.")
        return
    
    print(f"Using source directory: {source_dir}")
    
    # Create destination directory if it doesn't exist
    if not dest_dir.exists():
        os.makedirs(dest_dir)
        print(f"Created directory: {dest_dir}")
    
    # Create artist/album directories and move files
    supported_extensions = ['.mp3', '.m4a']
    processed_files = []  # Keep track of processed files to identify duplicates
    duplicate_count = 0
    duplicates_list = []
    
    # Create a dictionary to store album art already found
    # This helps avoid repeated API calls for the same album
    art_cache = {}
    
    for file in source_dir.glob("*.*"):
        if file.suffix.lower() not in supported_extensions:
            print(f"Skipping unsupported file: {file}")
            continue
            
        try:
            print(f"\nProcessing file: {file}")
            
            # Extract metadata
            metadata = extract_metadata(file)
            print(f"Extracted metadata: {metadata}")
            
            # Sanitize artist, album and title names
            artist_name = sanitize_filename(metadata['artist'])
            album_name = sanitize_filename(metadata['album'])
            title_name = sanitize_filename(metadata['title'])
            
            # Check for duplicates (same artist, album, and title)
            file_signature = f"{artist_name}|{album_name}|{title_name}"
            if file_signature in processed_files:
                duplicate_count += 1
                duplicates_list.append(f"{artist_name} - {album_name} - {title_name} ({file.name})")
                print(f"DUPLICATE FOUND: {artist_name} - {album_name} - {title_name}")
                print(f"Skipping duplicate file: {file}")
                if not args.force:
                    continue
                else:
                    print("Force mode enabled - overwriting existing file")
            
            processed_files.append(file_signature)
            
            # Create artist directory if it doesn't exist
            artist_dir = dest_dir / artist_name
            if not artist_dir.exists():
                os.makedirs(artist_dir)
                print(f"Created artist directory: {artist_dir}")
            
            # Check if this song already exists in another album folder for this artist
            # This prevents re-adding a song to "Unknown Album" that was previously identified
            song_already_exists = False
            if album_name == "Unknown Album":
                for album_folder in artist_dir.iterdir():
                    if album_folder.is_dir() and album_folder.name != "Unknown Album":
                        potential_file = album_folder / f"{title_name}{file.suffix}"
                        if potential_file.exists():
                            print(f"File already exists in a known album: {potential_file}")
                            print(f"Skipping to avoid duplicating in Unknown Album folder")
                            song_already_exists = True
                            break
                
                if song_already_exists and not args.force:
                    continue
            
            # Create album directory inside artist directory if it doesn't exist
            album_dir = artist_dir / album_name
            if not album_dir.exists():
                os.makedirs(album_dir)
                print(f"Created album directory: {album_dir}")
            
            # Extract and save album art if requested
            if args.extract_art:
                extract_and_save_album_art(file, album_dir)
            
            # Create new filename with just the title, preserving original extension
            new_filename = f"{title_name}{file.suffix}"
            
            # Destination path
            dest_path = album_dir / new_filename
            
            # Check if file already exists at destination
            if dest_path.exists() and not args.force:
                print(f"File already exists at destination: {dest_path}")
                print("Skipping to avoid overwriting. Use --force to override.")
                continue
            
            # Copy or move the file to destination
            if args.move:
                shutil.move(file, dest_path)
                print(f"Moved '{file.name}' to '{dest_path}'")
            else:
                shutil.copy2(file, dest_path)
                print(f"Copied '{file.name}' to '{dest_path}'")
            
            # If attach-art option is specified, try to attach album art to the file's metadata
            if args.attach_art:
                try:
                    # Check if the file already has album art
                    if not has_album_art(dest_path):
                        print(f"File doesn't have album art, attempting to find and attach: {dest_path}")
                        # Create a cache key for the album art
                        cache_key = f"{metadata['artist']}|{metadata['album']}"
                        
                        # Check if we already have album art for this artist/album
                        image_data = None
                        if cache_key in art_cache:
                            print(f"Using cached album art for {metadata['artist']} - {metadata['album']}")
                            image_data = art_cache[cache_key]
                        else:
                            # Search for album art online
                            image_data = search_album_art_online(metadata['artist'], metadata['album'], metadata['title'])
                            
                            if image_data:
                                # Cache the album art
                                art_cache[cache_key] = image_data
                                print(f"Found and cached album art for {metadata['artist']} - {metadata['album']}")
                            else:
                                print(f"Could not find album art online for {metadata['artist']} - {metadata['album']}")
                        
                        # If we found album art, attach it to the file
                        if image_data:
                            success = attach_album_art(dest_path, image_data)
                            if success:
                                print(f"Successfully attached album art to file: {dest_path}")
                            else:
                                print(f"Failed to attach album art to file: {dest_path}")
                    else:
                        print(f"File already has album art: {dest_path}")
                except Exception as e:
                    print(f"Error during album art attachment process: {e}")
                    # Continue processing other files even if album art attachment fails
                    pass
            
        except Exception as e:
            print(f"Error processing {file}: {e}")

    # Print summary of duplicates found
    if duplicate_count > 0:
        print("\n" + "="*50)
        print(f"Found {duplicate_count} duplicate files:")
        for duplicate in duplicates_list:
            print(f"  - {duplicate}")
        print("These files were skipped. Use --force to override.")
        print("="*50)
    
    # Clean up empty Unknown Album folders if not explicitly keeping them
    if not args.keep_empty:
        removed = clean_empty_unknown_album_folders(dest_dir, args.simulate)
        if removed > 0:
            print(f"Removed {removed} empty 'Unknown Album' folders")

if __name__ == "__main__":
    main()
    print("Music extraction and organization complete!")
