from flask import Flask, render_template, request, jsonify, send_file
import os
import math
import re
from collections import Counter
import difflib
from werkzeug.utils import secure_filename
import docx
import PyPDF2
import json
from io import StringIO
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATASET_FOLDER'] = 'dataset'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATASET_FOLDER'], exist_ok=True)

class AdvancedGrammarChecker:
    def __init__(self):
        self.grammar_rules = self.load_grammar_rules()
    
    def load_grammar_rules(self):
        """Load grammar rules and common corrections"""
        return {
            'spelling': {
                'recieve': 'receive',
                'seperate': 'separate',
                'definately': 'definitely',
                'occured': 'occurred',
                'untill': 'until',
                'adress': 'address',
                'alot': 'a lot',
                'becuase': 'because',
                'comming': 'coming',
                'existance': 'existence',
                'goverment': 'government',
                'happend': 'happened',
                'judgement': 'judgment',
                'knowlege': 'knowledge',
                'libary': 'library',
                'neccessary': 'necessary',
                'occassion': 'occasion',
                'prefered': 'preferred',
                'relevent': 'relevant',
                'sucess': 'success',
                'thier': 'their',
                'truely': 'truly',
                'writting': 'writing'
            },
            'grammar': {
                'i am': 'I am',
                'i have': 'I have',
                'i will': 'I will',
                'i would': 'I would',
                'cant': 'can\'t',
                'dont': 'don\'t',
                'wont': 'won\'t',
                'isnt': 'isn\'t',
                'doesnt': 'doesn\'t',
                'hasnt': 'hasn\'t',
                'havent': 'haven\'t',
                'hadnt': 'hadn\'t',
                'wouldnt': 'wouldn\'t',
                'shouldnt': 'shouldn\'t',
                'couldnt': 'couldn\'t'
            }
        }
    
    def calculate_text_stats(self, text):
        """Calculate comprehensive text statistics"""
        # Word count
        words = text.split()
        word_count = len(words)
        
        # Character count (with and without spaces)
        char_count_with_spaces = len(text)
        char_count_without_spaces = len(text.replace(' ', ''))
        
        # Sentence count
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Paragraph count
        paragraphs = [p for p in text.split('\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Reading time (assuming 200 words per minute)
        reading_time = word_count / 200
        
        return {
            'word_count': word_count,
            'char_count_with_spaces': char_count_with_spaces,
            'char_count_without_spaces': char_count_without_spaces,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_word_length': round(avg_word_length, 2),
            'reading_time_minutes': round(reading_time, 1)
        }
    
    def check_grammar_advanced(self, text):
        """Advanced grammar and spell checking with auto-correction capability"""
        issues = []
        corrected_text = text
        
        # Calculate text statistics
        text_stats = self.calculate_text_stats(text)
        
        # Split into sentences for better analysis
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence_idx, original_sentence in enumerate(sentences):
            if not original_sentence.strip():
                continue
                
            sentence = original_sentence
            words = sentence.split()
            
            # Check 1: Sentence capitalization
            if sentence and not sentence[0].isupper():
                issues.append({
                    'type': 'capitalization',
                    'original': sentence,
                    'corrected': sentence[0].upper() + sentence[1:] if sentence else sentence,
                    'position': sentence_idx,
                    'suggestion': 'Sentence should start with a capital letter'
                })
                # Auto-correct capitalization
                sentence = sentence[0].upper() + sentence[1:] if sentence else sentence
            
            # Check 2: Spelling mistakes
            for word_idx, word in enumerate(words):
                clean_word = re.sub(r'[^\w]', '', word.lower())
                
                if clean_word in self.grammar_rules['spelling']:
                    corrected_word = word.replace(clean_word, self.grammar_rules['spelling'][clean_word])
                    issues.append({
                        'type': 'spelling',
                        'original': word,
                        'corrected': corrected_word,
                        'position': f"{sentence_idx}.{word_idx}",
                        'suggestion': f'Correct spelling: {self.grammar_rules["spelling"][clean_word]}'
                    })
                    # Auto-correct spelling in sentence
                    sentence = sentence.replace(word, corrected_word)
            
            # Check 3: Common grammar mistakes
            for mistake, correction in self.grammar_rules['grammar'].items():
                if mistake in sentence.lower():
                    start_idx = sentence.lower().find(mistake)
                    original_phrase = sentence[start_idx:start_idx+len(mistake)]
                    corrected_phrase = correction
                    
                    issues.append({
                        'type': 'grammar',
                        'original': original_phrase,
                        'corrected': corrected_phrase,
                        'position': sentence_idx,
                        'suggestion': f'Use proper form: {correction}'
                    })
                    # Auto-correct grammar
                    sentence = sentence.replace(original_phrase, corrected_phrase)
            
            # Check 4: Multiple spaces
            if '  ' in sentence:
                issues.append({
                    'type': 'formatting',
                    'original': sentence,
                    'corrected': re.sub(r'\s+', ' ', sentence),
                    'position': sentence_idx,
                    'suggestion': 'Remove extra spaces'
                })
                sentence = re.sub(r'\s+', ' ', sentence)
            
            # Check 5: Missing spaces after punctuation
            sentence = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', sentence)
            
            # Update corrected text
            corrected_text = corrected_text.replace(original_sentence, sentence)
        
        # Check 6: Basic punctuation at end
        if corrected_text and corrected_text[-1] not in ['.', '!', '?']:
            issues.append({
                'type': 'punctuation',
                'original': corrected_text,
                'corrected': corrected_text + '.',
                'position': len(sentences) - 1,
                'suggestion': 'Add proper punctuation at the end'
            })
            corrected_text += '.'
        
        # Calculate statistics for corrected text
        corrected_stats = self.calculate_text_stats(corrected_text)
        
        # Count issues by type
        issue_counts = {
            'total': len(issues),
            'spelling': len([i for i in issues if i['type'] == 'spelling']),
            'grammar': len([i for i in issues if i['type'] == 'grammar']),
            'capitalization': len([i for i in issues if i['type'] == 'capitalization']),
            'formatting': len([i for i in issues if i['type'] == 'formatting']),
            'punctuation': len([i for i in issues if i['type'] == 'punctuation'])
        }
        
        # Calculate accuracy score
        total_words = text_stats['word_count']
        accuracy_score = max(0, 100 - (issue_counts['total'] * 2))  # Deduct 2% per issue
        
        return {
            'issues': issues,
            'corrected_text': corrected_text,
            'original_text': text,
            'text_stats': text_stats,
            'corrected_stats': corrected_stats,
            'issue_counts': issue_counts,
            'accuracy_score': round(accuracy_score, 1)
        }
    
    def auto_correct_text(self, text):
        """Automatically correct all detected issues"""
        result = self.check_grammar_advanced(text)
        return result['corrected_text']

class PlagiarismChecker:
    def __init__(self):
        self.dataset_texts = self.load_dataset()
        self.grammar_checker = AdvancedGrammarChecker()
    
    def load_dataset(self):
        """Load all text files from dataset folder"""
        dataset_texts = []
        dataset_path = app.config['DATASET_FOLDER']
        
        if os.path.exists(dataset_path):
            for filename in os.listdir(dataset_path):
                if filename.endswith('.txt'):
                    filepath = os.path.join(dataset_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as file:
                            content = file.read()
                            dataset_texts.append({
                                'filename': filename,
                                'content': content,
                                'tokens': self.preprocess_text(content)
                            })
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")
        
        return dataset_texts
    
    def preprocess_text(self, text):
        """Clean and tokenize text"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        tokens = text.split()
        return tokens
    
    def cosine_similarity(self, text1, text2):
        """Calculate cosine similarity between two texts"""
        vec1 = Counter(text1)
        vec2 = Counter(text2)
        
        all_words = set(vec1.keys()).union(set(vec2.keys()))
        vector1 = [vec1.get(word, 0) for word in all_words]
        vector2 = [vec2.get(word, 0) for word in all_words]
        
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(a * a for a in vector2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def jaccard_similarity(self, text1, text2):
        """Calculate Jaccard similarity between two texts"""
        set1 = set(text1)
        set2 = set(text2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def sequence_similarity(self, text1, text2):
        """Calculate sequence matching similarity"""
        seq_matcher = difflib.SequenceMatcher(None, ' '.join(text1), ' '.join(text2))
        return seq_matcher.ratio()
    
    def check_plagiarism(self, input_text):
        """Main function to check plagiarism with comprehensive stats"""
        input_tokens = self.preprocess_text(input_text)
        
        # Calculate text statistics
        text_stats = self.grammar_checker.calculate_text_stats(input_text)
        
        results = {
            'similarity_score': 0.0,
            'risk_level': 'Low',
            'matched_sources': [],
            'total_words': len(input_tokens),
            'grammar_issues': [],
            'recommendations': [],
            'corrected_text': input_text,
            'text_stats': text_stats,
            'issue_counts': {},
            'accuracy_score': 100
        }
        
        # Calculate similarities with dataset texts
        max_similarity = 0.0
        for dataset_text in self.dataset_texts:
            cosine_sim = self.cosine_similarity(input_tokens, dataset_text['tokens'])
            jaccard_sim = self.jaccard_similarity(input_tokens, dataset_text['tokens'])
            sequence_sim = self.sequence_similarity(input_tokens, dataset_text['tokens'])
            
            avg_similarity = (cosine_sim + jaccard_sim + sequence_sim) / 3
            
            if avg_similarity > 0.1:
                results['matched_sources'].append({
                    'filename': dataset_text['filename'],
                    'similarity': round(avg_similarity * 100, 2),
                    'cosine_similarity': round(cosine_sim * 100, 2),
                    'jaccard_similarity': round(jaccard_sim * 100, 2),
                    'sequence_similarity': round(sequence_sim * 100, 2)
                })
            
            if avg_similarity > max_similarity:
                max_similarity = avg_similarity
        
        results['similarity_score'] = round(max_similarity * 100, 2)
        
        # Determine risk level
        if results['similarity_score'] >= 70:
            results['risk_level'] = 'High'
        elif results['similarity_score'] >= 40:
            results['risk_level'] = 'Medium'
        else:
            results['risk_level'] = 'Low'
        
        # Check grammar using advanced checker
        grammar_result = self.grammar_checker.check_grammar_advanced(input_text)
        results['grammar_issues'] = grammar_result['issues']
        results['corrected_text'] = grammar_result['corrected_text']
        results['issue_counts'] = grammar_result['issue_counts']
        results['accuracy_score'] = grammar_result['accuracy_score']
        results['corrected_stats'] = grammar_result['corrected_stats']
        
        # Generate comprehensive recommendations
        results['recommendations'] = self.generate_recommendations(
            max_similarity, results['grammar_issues'], results['text_stats']
        )
        
        return results
    
    def generate_recommendations(self, similarity_score, grammar_issues, text_stats):
        """Generate comprehensive writing recommendations"""
        recommendations = []
        
        # Plagiarism recommendations
        if similarity_score > 0.7:
            recommendations.append("🚨 High plagiarism risk detected. Consider extensive paraphrasing.")
            recommendations.append("Add proper citations and references for matched content.")
        elif similarity_score > 0.4:
            recommendations.append("⚠️ Moderate similarity found. Review and paraphrase similar sections.")
            recommendations.append("Ensure all sources are properly cited.")
        else:
            recommendations.append("✅ Excellent originality! Your content is mostly unique.")
        
        # Grammar recommendations
        if grammar_issues:
            spelling_count = len([issue for issue in grammar_issues if issue['type'] == 'spelling'])
            grammar_count = len([issue for issue in grammar_issues if issue['type'] == 'grammar'])
            capitalization_count = len([issue for issue in grammar_issues if issue['type'] == 'capitalization'])
            
            if spelling_count > 0:
                recommendations.append(f"🔤 Found {spelling_count} spelling error(s). Use spell check carefully.")
            if grammar_count > 0:
                recommendations.append(f"📝 Found {grammar_count} grammar error(s). Review sentence structure.")
            if capitalization_count > 0:
                recommendations.append(f"🔠 Found {capitalization_count} capitalization issue(s). Check sentence starts.")
        
        # Writing style recommendations based on statistics
        if text_stats['avg_word_length'] > 6:
            recommendations.append("📊 Consider using simpler words for better readability.")
        elif text_stats['avg_word_length'] < 4:
            recommendations.append("📊 Your vocabulary is simple. Consider using more descriptive words.")
        
        if text_stats['sentence_count'] > 0:
            avg_sentence_length = text_stats['word_count'] / text_stats['sentence_count']
            if avg_sentence_length > 25:
                recommendations.append("📏 Sentences are quite long. Consider breaking them into shorter ones.")
            elif avg_sentence_length < 10:
                recommendations.append("📏 Sentences are very short. Try combining some for better flow.")
        
        # General recommendations
        recommendations.append("💡 Always proofread your work before final submission.")
        recommendations.append("📚 Use reliable sources and cite them properly.")
        recommendations.append("✍️ Consider using grammar tools for better writing quality.")
        
        return recommendations

# Initialize checkers
plagiarism_checker = PlagiarismChecker()

def extract_text_from_file(file_path, filename):
    """Extract text from different file formats"""
    if filename.endswith('.pdf'):
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    elif filename.endswith('.docx'):
        try:
            doc = docx.Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    
    elif filename.endswith('.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading TXT: {str(e)}"
    
    else:
        return "Unsupported file format"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract_text', methods=['POST'])
def extract_text():
    """Extract text from uploaded file and return for editing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        extracted_text = extract_text_from_file(file_path, filename)
        
        if extracted_text.startswith('Error'):
            return jsonify({'error': extracted_text})
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text,
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/check_grammar', methods=['POST'])
def check_grammar():
    """Check grammar only (without plagiarism check)"""
    try:
        text = request.json.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'})
        
        grammar_result = plagiarism_checker.grammar_checker.check_grammar_advanced(text)
        
        return jsonify({
            'success': True,
            'issues': grammar_result['issues'],
            'corrected_text': grammar_result['corrected_text'],
            'issues_count': len(grammar_result['issues']),
            'text_stats': grammar_result['text_stats'],
            'corrected_stats': grammar_result['corrected_stats'],
            'issue_counts': grammar_result['issue_counts'],
            'accuracy_score': grammar_result['accuracy_score']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/auto_correct', methods=['POST'])
def auto_correct():
    """Automatically correct all grammar issues"""
    try:
        text = request.json.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'})
        
        corrected_text = plagiarism_checker.grammar_checker.auto_correct_text(text)
        
        return jsonify({
            'success': True,
            'corrected_text': corrected_text
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/download_text', methods=['POST'])
def download_text():
    """Download the corrected text as a file"""
    try:
        data = request.json
        text = data.get('text', '')
        filename = data.get('filename', 'corrected_text.txt')
        
        if not text:
            return jsonify({'error': 'No text to download'})
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(text)
            temp_path = temp_file.name
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/check_plagiarism_full', methods=['POST'])
def check_plagiarism_full():
    """Full plagiarism and grammar check"""
    try:
        text = request.json.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'})
        
        results = plagiarism_checker.check_plagiarism(text)
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_text_stats', methods=['POST'])
def get_text_stats():
    """Get only text statistics without grammar check"""
    try:
        text = request.json.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'})
        
        stats = plagiarism_checker.grammar_checker.calculate_text_stats(text)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)