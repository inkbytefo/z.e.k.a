# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Kod Geliştirme Ajanı Modülü

import ast
import autopep8
import pylint.lint
import radon.complexity
import bandit
from typing import Dict, List, Any, Optional, Tuple
from ..core.agent_base import Agent

class CodeAnalysis:
    """Kod analizi sonuçları için veri sınıfı."""
    
    def __init__(self):
        self.style_issues: List[Dict[str, Any]] = []
        self.security_issues: List[Dict[str, Any]] = []
        self.complexity_score: float = 0.0
        self.maintainability_index: float = 0.0
        self.code_smells: List[Dict[str, Any]] = []

class CodingAgent(Agent):
    """Kod analizi ve geliştirme için ajan sınıfı."""
    
    def __init__(self, config: Dict[str, Any]):
        """CodingAgent başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        super().__init__(
            agent_id="coding_agent",
            name="Kod Asistanı",
            description="Kod analizi ve geliştirme yetenekleri için ajan",
            capabilities={
                "CODE_ANALYSIS",
                "CODE_FORMATTING",
                "SECURITY_SCAN",
                "OPTIMIZATION"
            }
        )
        
        self.config = config
        
        # Stil kontrolü için yapılandırma
        self.style_config = {
            "max_line_length": config.get("max_line_length", 100),
            "indent_size": config.get("indent_size", 4)
        }
        
        # Güvenlik taraması için yapılandırma
        self.security_config = {
            "confidence_threshold": config.get("security_confidence", 0.8),
            "severity_threshold": config.get("security_severity", "LOW")
        }
    
    def analyze_code(self, code: str) -> CodeAnalysis:
        """Kod analizi gerçekleştirir.
        
        Args:
            code: Analiz edilecek kod
            
        Returns:
            CodeAnalysis: Analiz sonuçları
        """
        analysis = CodeAnalysis()
        
        # Stil analizi (pylint)
        style_issues = self._check_style(code)
        analysis.style_issues = style_issues
        
        # Güvenlik taraması (bandit)
        security_issues = self._scan_security(code)
        analysis.security_issues = security_issues
        
        # Karmaşıklık analizi (radon)
        complexity = self._analyze_complexity(code)
        analysis.complexity_score = complexity.get("cyclomatic_complexity", 0)
        analysis.maintainability_index = complexity.get("maintainability_index", 0)
        
        # Kod kokuları
        code_smells = self._detect_code_smells(code)
        analysis.code_smells = code_smells
        
        return analysis
    
    def format_code(self, code: str) -> str:
        """Kodu belirtilen stil kurallarına göre formatlar.
        
        Args:
            code: Formatlanacak kod
            
        Returns:
            str: Formatlanmış kod
        """
        try:
            # PEP 8 formatlaması
            formatted_code = autopep8.fix_code(
                code,
                options={
                    "max_line_length": self.style_config["max_line_length"],
                    "indent_size": self.style_config["indent_size"]
                }
            )
            return formatted_code
            
        except Exception as e:
            raise RuntimeError(f"Kod formatlama hatası: {str(e)}")
    
    def optimize_code(self, code: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Kodu optimize eder ve öneriler sunar.
        
        Args:
            code: Optimize edilecek kod
            
        Returns:
            Tuple[str, List[Dict[str, Any]]]: Optimize edilmiş kod ve öneriler
        """
        try:
            # AST analizi
            tree = ast.parse(code)
            optimizer = self._create_optimizer()
            optimized_tree = optimizer.visit(tree)
            
            # Optimizasyon önerileri
            suggestions = self._generate_optimization_suggestions(tree)
            
            # Optimize edilmiş kodu oluştur
            optimized_code = ast.unparse(optimized_tree)
            
            return optimized_code, suggestions
            
        except Exception as e:
            raise RuntimeError(f"Kod optimizasyonu hatası: {str(e)}")
    
    def scan_security(self, code: str) -> List[Dict[str, Any]]:
        """Güvenlik taraması gerçekleştirir.
        
        Args:
            code: Taranacak kod
            
        Returns:
            List[Dict[str, Any]]: Güvenlik bulguları
        """
        return self._scan_security(code)
    
    def _check_style(self, code: str) -> List[Dict[str, Any]]:
        """Kod stil kontrolü gerçekleştirir."""
        issues = []
        try:
            # Pylint ile stil kontrolü
            reporter = pylint.lint.PyLinter()
            reporter.set_option("max-line-length", self.style_config["max_line_length"])
            reporter.check(code)
            
            for msg in reporter.reporter.messages:
                issues.append({
                    "line": msg.line,
                    "column": msg.column,
                    "type": msg.msg_id,
                    "message": msg.msg,
                    "severity": msg.category
                })
                
        except Exception as e:
            print(f"Stil kontrolü hatası: {str(e)}")
            
        return issues
    
    def _scan_security(self, code: str) -> List[Dict[str, Any]]:
        """Güvenlik taraması gerçekleştirir."""
        issues = []
        try:
            # Bandit ile güvenlik taraması
            findings = bandit.scan_str(
                code,
                confidence_level=self.security_config["confidence_threshold"],
                severity_level=self.security_config["severity_threshold"]
            )
            
            for finding in findings:
                issues.append({
                    "line": finding.lineno,
                    "severity": finding.severity,
                    "confidence": finding.confidence,
                    "message": finding.message,
                    "code": finding.code
                })
                
        except Exception as e:
            print(f"Güvenlik taraması hatası: {str(e)}")
            
        return issues
    
    def _analyze_complexity(self, code: str) -> Dict[str, float]:
        """Kod karmaşıklığını analiz eder."""
        try:
            # Radon ile karmaşıklık analizi
            cc = radon.complexity.cc_visit(code)
            mi = radon.complexity.mi_visit(code, True)
            
            return {
                "cyclomatic_complexity": sum(item.complexity for item in cc),
                "maintainability_index": mi
            }
            
        except Exception as e:
            print(f"Karmaşıklık analizi hatası: {str(e)}")
            return {"cyclomatic_complexity": 0.0, "maintainability_index": 0.0}
    
    def _detect_code_smells(self, code: str) -> List[Dict[str, Any]]:
        """Kod kokularını tespit eder."""
        smells = []
        try:
            tree = ast.parse(code)
            
            # Uzun metodlar
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.body) > 20:  # 20 satırdan uzun fonksiyonlar
                        smells.append({
                            "type": "long_method",
                            "name": node.name,
                            "line": node.lineno,
                            "message": "Fonksiyon çok uzun"
                        })
            
            # Çok parametre
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.args.args) > 5:  # 5'ten fazla parametre
                        smells.append({
                            "type": "too_many_parameters",
                            "name": node.name,
                            "line": node.lineno,
                            "message": "Çok fazla parametre"
                        })
                        
        except Exception as e:
            print(f"Kod kokusu tespiti hatası: {str(e)}")
            
        return smells
    
    def _create_optimizer(self) -> ast.NodeTransformer:
        """AST optimizasyonu için dönüştürücü oluşturur."""
        class Optimizer(ast.NodeTransformer):
            def visit_BinOp(self, node):
                # Sabit ifadeleri hesapla
                if (isinstance(node.left, ast.Constant) and
                    isinstance(node.right, ast.Constant)):
                    try:
                        result = ast.literal_eval(node)
                        return ast.Constant(value=result)
                    except:
                        pass
                return node
                
            def visit_If(self, node):
                # Ölü kodları temizle
                if isinstance(node.test, ast.Constant):
                    if node.test.value:
                        return node.body
                    else:
                        return node.orelse
                return node
        
        return Optimizer()
    
    def _generate_optimization_suggestions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Optimizasyon önerileri oluşturur."""
        suggestions = []
        
        for node in ast.walk(tree):
            # Gereksiz importları tespit et
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                suggestions.append({
                    "type": "import_check",
                    "line": node.lineno,
                    "message": "Import kullanımını kontrol edin"
                })
            
            # Tekrar eden hesaplamaları tespit et
            if isinstance(node, ast.BinOp):
                suggestions.append({
                    "type": "calculation_cache",
                    "line": node.lineno,
                    "message": "Sık tekrar eden hesaplamaları önbelleğe alın"
                })
        
        return suggestions
    
    async def process_task(
        self,
        task_id: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verilen görevi işler.
        
        Args:
            task_id: Görev ID'si
            description: Görev açıklaması
            metadata: Görev meta verileri
            
        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        try:
            task_type = metadata.get("type", "analyze")
            code = metadata.get("code")
            
            if not code:
                raise ValueError("Kod bulunamadı")
            
            if task_type == "analyze":
                analysis = self.analyze_code(code)
                return {
                    "task_id": task_id,
                    "status": "success",
                    "analysis": {
                        "style_issues": analysis.style_issues,
                        "security_issues": analysis.security_issues,
                        "complexity_score": analysis.complexity_score,
                        "maintainability_index": analysis.maintainability_index,
                        "code_smells": analysis.code_smells
                    }
                }
                
            elif task_type == "format":
                formatted_code = self.format_code(code)
                return {
                    "task_id": task_id,
                    "status": "success",
                    "formatted_code": formatted_code
                }
                
            elif task_type == "optimize":
                optimized_code, suggestions = self.optimize_code(code)
                return {
                    "task_id": task_id,
                    "status": "success",
                    "optimized_code": optimized_code,
                    "suggestions": suggestions
                }
                
            else:
                raise ValueError(f"Desteklenmeyen görev tipi: {task_type}")
                
        except Exception as e:
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
